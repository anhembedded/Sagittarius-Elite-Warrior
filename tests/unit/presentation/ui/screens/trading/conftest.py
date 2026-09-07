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

`BUG-107` moved the byte-identical `mock_config`/`container`/`view`/
`presenter` copies here too, for the same reason the real objects came
here: the bug shipped because no test drove the arming button, and a
fourth hand-rolled copy of the same four fixtures is what stood between
that test and being written. `test_trading_presenter_equity.py` keeps its
own `container` — it binds `IEventBus` so it can assert on it, which is a
real difference, not a copy.
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
from Sagittarius_Elite_Warrior.src.presentation.ui.screens.trading.trading_presenter import (
    TradingPresenter,
)
from sagittarius_engine.extensions.pyside_mvc.base_view import DEV_MODE_CONFIG_KEY
from sagittarius_engine.interfaces.i_config import IConfig
from sagittarius_engine.interfaces.i_dispatcher import IDispatcher
from sagittarius_engine.interfaces.i_thread_manager import IThreadManager

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


# ---------------------------------------------------------------------- #
# The mocked boundaries, and the Presenter built on top of them.
#
# `view` is a `MagicMock` (not a real `TradingView`) — `TradingPresenter`
# never does `hasattr`/`getattr` capability probing on it, and the real
# View's own construction is already covered by
# `test_trading_view_contract.py`.
# ---------------------------------------------------------------------- #


@pytest.fixture
def mock_config() -> MagicMock:
    config = MagicMock()
    config.get_all.return_value = {
        "DEFAULT_SYMBOLS": ["BTCUSDT"],
        "DEFAULT_INTERVAL": "1m",
    }
    config.get.side_effect = lambda key, default=None, cast=None: (
        True if key == DEV_MODE_CONFIG_KEY else default
    )
    return config


@pytest.fixture
def container(
    mock_config,
    mock_dispatcher,
    mock_thread_manager,
    session_state,
    equity_recorder,
    strategy_session,
    strategy_registry,
    make_container,
):
    # `BOT-125` review — one shared fake, so adding a Presenter
    # dependency stops costing one edit per test module.
    return make_container(
        {
            IConfig: mock_config,
            IDispatcher: mock_dispatcher,
            IThreadManager: mock_thread_manager,
            TradingSessionState: session_state,
            EquityCurveRecorder: equity_recorder,
            LiveStrategySession: strategy_session,
            StrategyRegistry: strategy_registry,
        }
    )


@pytest.fixture
def view() -> MagicMock:
    return MagicMock()


@pytest.fixture
def presenter(qapp, view, container, mock_thread_manager) -> TradingPresenter:
    """Construction itself submits `ChartCoordinator.start()`'s background
    work (loading history for the default symbol) — reset the mock
    afterward so each test's own `assert_called_once()` reflects only what
    that test triggered, same reasoning `test_dashboard_presenter.py`'s own
    `presenter` fixture documents."""
    p = TradingPresenter(view, container)
    mock_thread_manager.submit.reset_mock()
    return p
