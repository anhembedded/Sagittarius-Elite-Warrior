"""Shared fixtures for the Trading screen's presenter tests.

`EPIC-022D` added two collaborators every one of those tests now resolves
(`LiveStrategySession`, `StrategyRegistry`), and the three test modules
each had their own hand-rolled `container` fixture. Rather than paste the
same two branches into all three, the pieces that must be REAL objects
live here.

They have to be real, not `MagicMock()`: `StrategyArmingCoordinator` reads
`session.config` and formats it into the card's summary line, and a
`MagicMock` config formats into `<MagicMock id=...>` — a test suite that
green-lights that would be asserting on nonsense.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from Sagittarius_Elite_Warrior.src.application.services.equity_curve_recorder import (
    EquityCurveRecorder,
)
from Sagittarius_Elite_Warrior.src.application.services.live_strategy_factory import (
    LiveStrategyFactory,
)
from Sagittarius_Elite_Warrior.src.application.services.live_strategy_session import (
    LiveStrategySession,
)
from Sagittarius_Elite_Warrior.src.application.services.strategy_registry import (
    StrategyRegistry,
)
from Sagittarius_Elite_Warrior.src.application.services.trading_session_state import (
    TradingSessionState,
)
from Sagittarius_Elite_Warrior.src.domain.strategies.ema_crossover_strategy import (
    EmaCrossoverStrategy,
)

#: One real registered strategy is enough for every assertion these tests
#: make, and keeps them independent of how many strategies the app ships.
TEST_STRATEGY_KEY = "ema_crossover"


@pytest.fixture
def strategy_registry() -> StrategyRegistry:
    registry = StrategyRegistry()
    registry.register(TEST_STRATEGY_KEY, EmaCrossoverStrategy)
    return registry


@pytest.fixture
def strategy_session(strategy_registry: StrategyRegistry) -> LiveStrategySession:
    """A real session over a real registry, with only the network-facing
    collaborators mocked — so arming really validates parameters against
    the real strategy."""
    factory = LiveStrategyFactory(
        strategy_registry,
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    return LiveStrategySession(factory)


# --------------------------------------------------------------------- #
# Collaborators the three Presenter modules each declared identically
#
# `test-health` C7: the same four fixtures were byte-identical in
# `test_trading_presenter_toggle.py`, `..._emergency_stop.py` and
# `..._equity.py`. Not four opinions about a session state — one, copied
# three times, with nothing keeping the copies in step.
# --------------------------------------------------------------------- #


@pytest.fixture
def session_state() -> TradingSessionState:
    return TradingSessionState()


@pytest.fixture
def equity_recorder() -> EquityCurveRecorder:
    return EquityCurveRecorder()


@pytest.fixture
def mock_thread_manager() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_dispatcher() -> MagicMock:
    return MagicMock()
