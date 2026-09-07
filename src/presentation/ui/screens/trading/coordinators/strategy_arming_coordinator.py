"""`EPIC-022D`/`EPIC-022F` — the Trading screen's strategy card, minus the
widgets.

@details Holds the parameter values the user is editing, turns the card's
two buttons into `ArmStrategyCommand`/`DisarmStrategyCommand`, and
persists a successful arming to `IConfig` so the next session starts from
the same choice.

Split out of `TradingPresenter` rather than added to it: that file was
already 729 lines before this feature, and `async-ui-action-rule.md` §2
says a Presenter whose background-action logic outgrows one file splits
by feature slice. Per that same section this Coordinator owns **no**
action-id/cancellation bookkeeping — `TradingPresenter` keeps the single
`ActionOwnershipTracker` and calls in here; nothing below starts its own
background work.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from typing import Any

from Sagittarius_Elite_Warrior.src.application.use_cases.trading.arm_strategy import (
    ArmStrategyBlockReason,
    ArmStrategyCommand,
    ArmStrategyResult,
)
from Sagittarius_Elite_Warrior.src.application.use_cases.trading.disarm_strategy import (
    DisarmStrategyCommand,
    DisarmStrategyResult,
)
from Sagittarius_Elite_Warrior.src.config.config_keys import ConfigKeys
from Sagittarius_Elite_Warrior.src.domain.value_objects.live_strategy_config import (
    DEFAULT_LEVERAGE,
    DEFAULT_SIZING_PERCENT,
    LiveStrategyConfig,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.components.strategy_params import (
    build_bot_params_rows,
    build_bot_params_schema,
    parse_bot_params,
)

logger = logging.getLogger("App.TradingStrategyArming")

#: Vietnamese copy for each refusal. Every branch of
#: `ArmStrategyBlockReason` has a line here — a missing one would surface
#: as a silent no-op button, which is the failure mode this whole epic
#: exists to remove.
ARM_BLOCK_MESSAGES: dict[ArmStrategyBlockReason, str] = {
    ArmStrategyBlockReason.TRADING_IS_ENABLED: (
        "Đang giao dịch — hãy tắt giao dịch trước khi đổi chiến lược."
    ),
    ArmStrategyBlockReason.STRATEGY_NOT_FOUND: (
        "Không tìm thấy chiến lược này trong danh sách đã đăng ký."
    ),
    ArmStrategyBlockReason.INVALID_PARAMS: "Thông số Chiến lược không hợp lệ.",
    ArmStrategyBlockReason.MISSING_SYMBOL_OR_INTERVAL: (
        "Cần chọn cả symbol và khung thời gian giao dịch."
    ),
}
DISARM_BLOCKED_MESSAGE = "Đang giao dịch — hãy tắt giao dịch trước khi gỡ chiến lược."


def humanize_strategy_key(key: str) -> str:
    """`ema_crossover` -> `Ema Crossover`.

    @details Same transformation `BackTestPresenter._humanize_strategy_key`
    applies, and for the same reason: `BaseStrategy` declares no display
    name, so the key is all there is. Duplicated as a two-line pure
    function rather than imported across screens — importing
    `screens/backtest/` from `screens/trading/` is the dependency
    direction `EPIC-021L` removed. If a third caller appears, or
    strategies ever declare a real display name, this is the place that
    becomes a shared lookup.
    """
    return key.replace("_", " ").title()


class StrategyArmingCoordinator:
    """@brief Strategy selection, parameters, arming and persistence for
    the Trading screen."""

    def __init__(
        self,
        view_model,
        config,
        dispatcher,
        available_strategies: Callable[[], Mapping[str, type]],
        get_active_symbol: Callable[[], str],
    ) -> None:
        self._view_model = view_model
        self._config = config
        self._dispatcher = dispatcher
        self._available_strategies = available_strategies
        self._get_active_symbol = get_active_symbol
        self._params: dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # Restore (`EPIC-022F`)
    # ------------------------------------------------------------------ #

    def restore_into_view_model(self, interval_options: list[str]) -> None:
        """Fills the card from `trading.live_*` — and does nothing else.

        @details No `ArmStrategyCommand`, no `EnableTradingCommand`, no
        network call. `BUG-101` (a Backtest restore that fired a real
        200k-row query because it went through the same setters a user
        does) and `BUG-104` (a remembered route that started a live
        stream on boot) are the same bug twice; this method is written to
        not be its third occurrence. After a restore the screen shows the
        saved choice and nothing is armed, so the user still has to press
        "Nạp chiến lược" themselves.
        """
        available = sorted(self._available_strategies())
        self._view_model.set_strategy_options(
            [{"key": key, "label": humanize_strategy_key(key)} for key in available],
            interval_options,
        )
        saved_key = str(
            self._config.get(ConfigKeys.TRADING_LIVE_STRATEGY_KEY.value, "")
        )
        if saved_key not in available:
            # A saved key that no longer exists (renamed, removed) must
            # not be shown as if it were selectable. The combo falls back
            # to the first real strategy so the card is never empty — but
            # nothing is armed either way, so the fallback can only ever
            # become live if the user presses "Nạp chiến lược" on it.
            saved_key = available[0] if available else ""
        self._params = self._read_saved_params()
        self._view_model.set_strategy_selection(
            saved_key,
            str(self._config.get(ConfigKeys.TRADING_LIVE_INTERVAL.value, "")),
            float(
                self._config.get(
                    ConfigKeys.TRADING_LIVE_SIZING_PERCENT.value,
                    DEFAULT_SIZING_PERCENT,
                )
            ),
            float(
                self._config.get(
                    ConfigKeys.TRADING_LIVE_LEVERAGE.value, DEFAULT_LEVERAGE
                )
            ),
        )
        self.refresh_params_rows()

    def _read_saved_params(self) -> dict[str, Any]:
        raw = str(self._config.get(ConfigKeys.TRADING_LIVE_STRATEGY_PARAMS.value, ""))
        if not raw:
            return {}
        try:
            stored = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Bỏ qua thông số chiến lược đã lưu — không đọc được JSON.")
            return {}
        return stored if isinstance(stored, dict) else {}

    # ------------------------------------------------------------------ #
    # "Thông số Chiến lược"
    # ------------------------------------------------------------------ #

    def refresh_params_rows(self) -> None:
        """Rebuilds the parameter form for whatever strategy is selected."""
        strategy_cls = self._selected_strategy_class()
        if strategy_cls is None:
            self._view_model.set_bot_params([], [])
            return
        schema = build_bot_params_schema(strategy_cls, self._params)
        self._view_model.set_bot_params(schema, build_bot_params_rows(schema))
        self._view_model.set_bot_params_error("")

    def apply_params(self, raw_values: Mapping[str, Any]) -> bool:
        """@returns Whether the values were accepted.

        @details Validation is `parse_bot_params` against the strategy's
        own declared `inputs` — the same call the Backtest screen makes,
        so a value accepted on one screen cannot be rejected on the other.
        """
        strategy_cls = self._selected_strategy_class()
        if strategy_cls is None:
            return False
        try:
            parsed = parse_bot_params(strategy_cls().inputs, raw_values)
        except ValueError as exc:
            self._view_model.set_bot_params_error(str(exc))
            return False
        self._params = dict(parsed)
        self._view_model.set_bot_params_error("")
        self.refresh_params_rows()
        return True

    def _selected_strategy_class(self) -> type | None:
        return self._available_strategies().get(self._view_model.selectedStrategyKey)

    # ------------------------------------------------------------------ #
    # Arm / disarm
    # ------------------------------------------------------------------ #

    def build_config(self) -> LiveStrategyConfig:
        return LiveStrategyConfig(
            strategy_key=self._view_model.selectedStrategyKey,
            symbol=self._get_active_symbol(),
            interval=self._view_model.liveInterval,
            strategy_params=dict(self._params),
            sizing_percent=self._view_model.sizingPercent,
            leverage=self._view_model.leverage,
        )

    def arm(self) -> ArmStrategyResult:
        """Runs `ArmStrategyCommand`; persists only on success.

        @details Persisting only a successful arming is deliberate: a
        half-typed parameter set that the strategy rejected is not a
        configuration worth reloading next session, and writing it would
        make the next boot's `_arm_from_config` fail the same way with no
        user around to see why.
        """
        result = self._dispatcher.dispatch(ArmStrategyCommand(self.build_config()))
        if result.armed:
            self._persist()
        return result

    def disarm(self) -> DisarmStrategyResult:
        return self._dispatcher.dispatch(DisarmStrategyCommand())

    def _persist(self) -> None:
        config = self.build_config()
        self._config.set(
            ConfigKeys.TRADING_LIVE_STRATEGY_KEY.value, config.strategy_key
        )
        self._config.set(ConfigKeys.TRADING_LIVE_SYMBOL.value, config.symbol)
        self._config.set(ConfigKeys.TRADING_LIVE_INTERVAL.value, config.interval)
        self._config.set(
            ConfigKeys.TRADING_LIVE_STRATEGY_PARAMS.value,
            json.dumps(dict(config.strategy_params), sort_keys=True),
        )
        self._config.set(
            ConfigKeys.TRADING_LIVE_SIZING_PERCENT.value, config.sizing_percent
        )
        self._config.set(ConfigKeys.TRADING_LIVE_LEVERAGE.value, config.leverage)
        # `save()` belongs to `ConfigManager`, not to the `IConfig` port —
        # same duck-check `SettingsPresenter` uses, so a config
        # implementation without it degrades to "kept for this session"
        # rather than raising.
        save = getattr(self._config, "save", None)
        if callable(save):
            save()

    def armed_summary(self, config: LiveStrategyConfig | None) -> str:
        """One line describing what is actually running, or "" for nothing.

        @details Includes the parameters, not just the strategy name: two
        armings of the same strategy with different periods are different
        bots, and a summary that could not tell them apart would be the
        `armedSummary`-shaped version of the untruthful UI this epic set
        out to fix.
        """
        if config is None:
            return ""
        parts = [
            humanize_strategy_key(config.strategy_key),
            f"{config.symbol} {config.interval}",
            f"{config.sizing_percent:g}%/lệnh",
            f"{config.leverage:g}x",
        ]
        if config.strategy_params:
            parts.append(
                ", ".join(
                    f"{name}={value}"
                    for name, value in sorted(config.strategy_params.items())
                )
            )
        return " · ".join(parts)
