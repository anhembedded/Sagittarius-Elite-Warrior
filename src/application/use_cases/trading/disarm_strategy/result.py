"""`EPIC-022B` — the outcome of one `DisarmStrategyCommand`."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DisarmStrategyBlockReason(str, Enum):
    """@brief Why the strategy was not cleared."""

    #: Live trading is currently ON. Disarming would leave trading
    #: "enabled" with nothing generating signals — the exact dishonest
    #: state `EPIC-022` set out to remove (`EnableTradingBlockReason.
    #: NO_STRATEGY_ARMED` refuses to *enter* it; this refuses to reach it
    #: from the other direction). An open position would also be left
    #: with no strategy planning its exit.
    TRADING_IS_ENABLED = "trading_is_enabled"


@dataclass(frozen=True)
class DisarmStrategyResult:
    disarmed: bool
    block_reason: DisarmStrategyBlockReason | None = None
