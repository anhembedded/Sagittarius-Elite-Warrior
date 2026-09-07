"""`EPIC-022A` — what the user chose to run live, as plain data.

@details Deliberately holds **no live objects** (no `StrategyEngine`, no
`LiveTradingCoordinator`): this is the value that gets compared, logged,
persisted to `IConfig` and restored next session, and a value object that
also carried a running engine could not do any of those things. Building
the engine pair from one of these is `LiveStrategyFactory`'s job, and
holding the built pair is `LiveStrategySession`'s.

`strategy_params` is stored as an immutable `MappingProxyType` snapshot
rather than the caller's dict — the UI keeps editing its own dict while
the user types, and an armed config that silently changed underneath the
running engine would make "what is actually running" unanswerable.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

#: `EPIC-021G`'s own defaults, repeated here as the value object's own
#: floor so a config missing these keys still produces a usable arming
#: rather than a `TypeError` at construction.
DEFAULT_SIZING_PERCENT = 20.0
DEFAULT_LEVERAGE = 1.0


@dataclass(frozen=True)
class LiveStrategyConfig:
    """@brief One complete answer to "what should the bot run right now".

    @details Every field a user picks on the Trading screen's strategy
    card, plus nothing else. `symbol`/`interval` are part of the config,
    not separate state, because `MarketTickEventHandler`'s single-symbol/
    single-interval rule (`BUG-085`) makes them inseparable from the
    engine: changing either one requires the same rebuild that changing
    the strategy does.
    """

    strategy_key: str
    symbol: str
    interval: str
    strategy_params: Mapping[str, Any] = field(default_factory=dict)
    sizing_percent: float = DEFAULT_SIZING_PERCENT
    leverage: float = DEFAULT_LEVERAGE

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "strategy_params", MappingProxyType(dict(self.strategy_params))
        )

    @property
    def is_complete(self) -> bool:
        """@brief Whether this names a runnable target at all.

        @details `boot()` historically gated on
        `if live_symbol and live_strategy_key and live_interval` — the same
        three-way check, now asked of the value itself instead of being
        re-typed at each call site.
        """
        return bool(self.strategy_key and self.symbol and self.interval)
