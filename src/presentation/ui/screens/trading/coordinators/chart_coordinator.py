"""Historical load + live-stream lifecycle for the Trading screen's single
chart (`EPIC-021I`).

@details Mirrors `dashboard/stream_lifecycle_controller.py`'s shape,
narrowed: one chart, one symbol/interval at a time, no auto-sync progress
bar (this screen has none — plain log lines instead), no Load History /
Start Live distinction (the chart is always live while this screen is
open).

Never touches `TradingPresenter.view` — every method here runs on a
background thread (submitted via `IThreadManager`), and `ChartCard` is a
`QWidget`; mutating it off the Qt main thread is the exact class of defect
`BUG-031` documents. Results are reported back only through the
`emit_*` callables, each bound to one of `TradingPresenter`'s own Qt
signals — the same boundary `StreamLifecycleController` uses.

Owns no async action-id/cancellation bookkeeping of its own
(`async-ui-action-rule.md` §2): the `CancellationToken` is created and
reset by `TradingPresenter`, passed in on every call.

**Cross-screen caveat.** `ILiveStreamService` (behind
`StartLiveStreamCommand`/`StopLiveStreamCommand`) is one process-wide
stream, not one per screen — confirmed by reading
`i_live_stream_service.py`: `start_stream(symbols, interval)` takes no
caller identity, and `stop_stream()` takes no arguments at all. Opening
Dev Board and Trading at the same time means whichever screen last called
`StartLiveStreamCommand` decides which symbol's ticks reach BOTH charts;
`stop()` here, called on this screen's own symbol/interval change, stops
that shared stream outright, including for Dev Board if it happens to be
running. This is a pre-existing architectural constraint, not a
regression this build introduces — Dev Board's own `_on_timeframe_changed`
already does the identical stop-then-start dance for exactly the same
reason. Multiplexing a real per-screen stream is out of scope for this
epic; see this task's own write-up for the follow-up.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from Sagittarius_Elite_Warrior.src.application.use_cases.queries.get_historical_klines.query import (
    GetHistoricalKlinesQuery,
)
from Sagittarius_Elite_Warrior.src.application.use_cases.stream.start_live_stream.command import (
    StartLiveStreamCommand,
)
from Sagittarius_Elite_Warrior.src.application.use_cases.stream.stop_live_stream.command import (
    StopLiveStreamCommand,
)
from Sagittarius_Elite_Warrior.src.application.use_cases.sync.sync_market_data.command import (
    SyncMarketDataCommand,
)
from Sagittarius_Elite_Warrior.src.domain.value_objects.timeframe import TimeFrame
from Sagittarius_Elite_Warrior.src.presentation.ui.components.chart_card.kline_mapping import (
    map_klines,
    map_volume,
)

if TYPE_CHECKING:
    from sagittarius_engine.interfaces.i_dispatcher import IDispatcher
    from sagittarius_engine.interfaces.i_thread_manager import IThreadManager
    from sagittarius_engine.runtime.tasks.cancellation_token import CancellationToken

#: How many candles the chart asks for on a (re)load — a fixed depth, not
#: derived from anything (unlike Dev Board's `_compute_fetch_limit()`,
#: which grows with enabled indicator scripts — this screen has none,
#: EPIC-021I's own scope decision).
_HISTORY_CANDLE_LIMIT = 500


class ChartCoordinator:
    """@brief Loads history and keeps the Trading screen's one `ChartCard`
    live for whatever symbol/interval is currently selected."""

    def __init__(
        self,
        *,
        thread_manager: IThreadManager,
        dispatcher: IDispatcher,
        emit_history_ready: Callable[[str, list, list, list], None],
        emit_load_finished: Callable[[], None],
        emit_stream_started: Callable[[str], None],
        emit_stream_failed: Callable[[str], None],
        emit_log: Callable[[str], None],
    ) -> None:
        self._thread_manager = thread_manager
        self._dispatcher = dispatcher
        self._emit_history_ready = emit_history_ready
        self._emit_load_finished = emit_load_finished
        self._emit_stream_started = emit_stream_started
        self._emit_stream_failed = emit_stream_failed
        self._emit_log = emit_log

    def start(
        self,
        symbol: str,
        interval_str: str,
        token: CancellationToken,
        *,
        go_live: bool = False,
    ) -> None:
        """Submits the chart load for `symbol`/`interval_str`.

        @param go_live When `False` (the default) this reads **local history
        only** — one `GetHistoricalKlinesQuery` against the app's own
        database, no network. When `True` it also syncs from Binance and
        opens the websocket.

        @details `BUG-107`: opening a screen is not a request to go on the
        network. `go_live` defaults to `False` so a caller that forgets the
        argument gets the quiet behaviour, not a live stream — the failure
        this parameter exists to prevent should not be reachable by
        omission.
        """
        self._thread_manager.submit(self._run, symbol, interval_str, token, go_live)

    def stop(self) -> None:
        """Fast and synchronous — same as Dev Board's own
        `_on_stop_stream`, which never submits this to the thread pool
        either."""
        self._dispatcher.dispatch(StopLiveStreamCommand, StopLiveStreamCommand())

    def _run(
        self,
        symbol: str,
        interval_str: str,
        token: CancellationToken,
        go_live: bool,
    ) -> None:
        try:
            interval = TimeFrame(interval_str)

            if not go_live:
                self._emit_log(
                    f"Đang tải dữ liệu {symbol} từ cơ sở dữ liệu cục bộ "
                    "(chưa kết nối trực tiếp — bật giao dịch để kết nối)."
                )

            if go_live:
                self._emit_log(f"Đang đồng bộ dữ liệu {symbol} từ Binance...")
                self._dispatcher.dispatch(
                    SyncMarketDataCommand,
                    SyncMarketDataCommand(
                        symbols=[symbol],
                        interval=interval,
                        cancellation_requested=token.is_cancelled,
                    ),
                )
                if token.is_cancelled():
                    return

            self._load_history(symbol, interval)
            if token.is_cancelled():
                return

            if go_live:
                self._start_stream(symbol, interval)
        except Exception as exc:  # noqa: BLE001 - worker boundary: report the real failure instead of losing it to a background-thread traceback
            self._emit_stream_failed(f"Lỗi hệ thống: {exc}")
        finally:
            self._emit_load_finished()

    def _load_history(self, symbol: str, interval: TimeFrame) -> None:
        query = GetHistoricalKlinesQuery(
            symbol=[symbol],
            interval=interval,
            limit=_HISTORY_CANDLE_LIMIT,
            order_by_desc=True,
        )
        response = self._dispatcher.dispatch(GetHistoricalKlinesQuery, query)
        results = getattr(response, "data", response) if response else {}
        klines = results.get(symbol, []) if isinstance(results, dict) else []
        if not klines:
            self._emit_log(f"Không có dữ liệu lịch sử cho {symbol}.")
            return
        ordered = list(reversed(klines))
        # `EPIC-022E` — the raw `MarketData` rows ride along beside the
        # chart-shaped tuples. `StrategyOverlayCoordinator` replays the
        # strategy over real candles (it reads `close_time`/`close_price`),
        # which `map_klines`' 5-tuples no longer carry; re-fetching them
        # for the overlay would be a second identical query.
        self._emit_history_ready(
            symbol, map_klines(ordered), map_volume(ordered), ordered
        )

    def _start_stream(self, symbol: str, interval: TimeFrame) -> None:
        self._emit_log(f"Đang mở luồng trực tiếp cho {symbol}...")
        cmd = StartLiveStreamCommand(symbols=[symbol], interval=interval)
        response = self._dispatcher.dispatch(StartLiveStreamCommand, cmd)
        if response and getattr(response, "success", True):
            self._emit_stream_started(f"Đang truyền dữ liệu trực tiếp cho {symbol}.")
        else:
            message = getattr(response, "message", "Unknown error")
            self._emit_stream_failed(f"Không thể mở luồng trực tiếp: {message}")
