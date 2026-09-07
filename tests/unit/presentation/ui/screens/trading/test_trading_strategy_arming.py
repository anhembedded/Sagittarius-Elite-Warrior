"""`EPIC-022D`/`EPIC-022F` — the Trading screen's strategy card.

The assertions here are mostly about what must NOT happen: picking a
strategy must not arm it, restoring config must not run anything, and a
refusal must reach the user as words rather than as a button that appears
to do nothing. Those are the failure modes this epic was opened to fix.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from Sagittarius_Elite_Warrior.src.application.use_cases.trading.arm_strategy import (
    ArmStrategyBlockReason,
    ArmStrategyCommand,
    ArmStrategyResult,
)
from Sagittarius_Elite_Warrior.src.application.use_cases.trading.disarm_strategy import (
    DisarmStrategyBlockReason,
    DisarmStrategyCommand,
    DisarmStrategyResult,
)
from Sagittarius_Elite_Warrior.src.config.config_keys import ConfigKeys
from Sagittarius_Elite_Warrior.src.domain.value_objects.live_strategy_config import (
    LiveStrategyConfig,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.common.action_ownership_tracker import (
    ActionOutcome,
    ActionOwnershipTracker,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.common.strategy_display import (
    humanize_strategy_key,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.screens.trading.coordinators.strategy_arming_coordinator import (
    ARM_BLOCK_MESSAGES,
    StrategyArmingCoordinator,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.screens.trading.trading_view_model import (
    TradingViewModel,
)

#: Mirrors `conftest.TEST_STRATEGY_KEY`. Restated rather than imported:
#: the test package has no `__init__.py`, so a relative import from a
#: conftest is not a package import at all.
TEST_STRATEGY_KEY = "ema_crossover"

_INTERVALS = ["1m", "5m", "1h"]

#: The action kind `TradingPresenter` hands the Coordinator (`_ARM_ACTION`).
#: Any string works; what matters is that the same one comes back out of
#: the tracker, which is what proves the button really registered its
#: action instead of failing before it got that far.
_ARM_ACTION = "arm_strategy"


class _FakeConfig:
    """A config that really stores what it is given, so a persistence test
    can assert on the values rather than on `set` having been called."""

    def __init__(self, initial: dict | None = None) -> None:
        self.values = dict(initial or {})
        self.save_count = 0

    def get(self, key, default=None, cast=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        self.save_count += 1


@pytest.fixture
def view_model(qapp) -> TradingViewModel:
    return TradingViewModel()


@pytest.fixture
def dispatcher() -> MagicMock:
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = ArmStrategyResult(armed=True)
    return dispatcher


def _coordinator(
    view_model,
    dispatcher,
    strategy_registry,
    config=None,
    armed=None,
    tracker=None,
    status_sink=None,
):
    """@param armed What the session reports as armed, for the tests that
    exercise the summary/status path. Everything the Presenter used to do
    inline is now handed in, so these tests drive the same code the real
    button does rather than a coordinator missing half its collaborators.

    @param tracker The Presenter-owned tracker, handed in exactly as
    `TradingPresenter` hands its `_arm_tracker` in. Tests that assert on
    action ownership pass their own so they can read it back; the rest get
    a real one — never a `Mock`, which would accept any method name at all
    and is precisely how `BUG-107` reached a user (`bug-fix-rule.md` §3).

    @param status_sink A list collecting `(message, is_error)` as the
    button reports it, so a test can assert the user is actually told
    something rather than only that a command was dispatched.
    """

    def _set_status(message, is_error):
        if status_sink is not None:
            status_sink.append((message, is_error))

    return StrategyArmingCoordinator(
        view_model=view_model,
        config=config or _FakeConfig(),
        dispatcher=dispatcher,
        available_strategies=strategy_registry.available,
        get_active_symbol=lambda: "BTCUSDT",
        get_armed_config=lambda: armed,
        tracker=tracker or ActionOwnershipTracker(),
        arm_action_kind=_ARM_ACTION,
        set_status=_set_status,
        append_log=lambda _line: None,
        on_armed_changed=lambda _config, _busy: None,
    )


def test_restore_fills_the_card_without_dispatching_anything(
    view_model, dispatcher, strategy_registry
):
    """`BUG-101`/`BUG-104` were both "restoring config quietly ran real
    work". This is the assertion that stops the third occurrence."""
    config = _FakeConfig(
        {
            ConfigKeys.TRADING_LIVE_STRATEGY_KEY.value: TEST_STRATEGY_KEY,
            ConfigKeys.TRADING_LIVE_INTERVAL.value: "5m",
            ConfigKeys.TRADING_LIVE_SIZING_PERCENT.value: 7.5,
            ConfigKeys.TRADING_LIVE_LEVERAGE.value: 3.0,
            ConfigKeys.TRADING_LIVE_STRATEGY_PARAMS.value: '{"fast_period": 8}',
        }
    )
    coordinator = _coordinator(view_model, dispatcher, strategy_registry, config)

    coordinator.restore_into_view_model(_INTERVALS)

    assert view_model.selectedStrategyKey == TEST_STRATEGY_KEY
    assert view_model.liveInterval == "5m"
    assert view_model.sizingPercent == 7.5
    assert view_model.leverage == 3.0
    dispatcher.dispatch.assert_not_called()


def test_restore_leaves_nothing_armed(view_model, dispatcher, strategy_registry):
    """The card shows the saved choice; the engine stays empty until the
    user presses "Nạp chiến lược" themselves."""
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)

    coordinator.restore_into_view_model(_INTERVALS)

    assert view_model.armedSummary == ""


def test_a_saved_key_that_no_longer_exists_falls_back_without_arming(
    view_model, dispatcher, strategy_registry
):
    config = _FakeConfig(
        {ConfigKeys.TRADING_LIVE_STRATEGY_KEY.value: "strategy_deleted_last_year"}
    )
    coordinator = _coordinator(view_model, dispatcher, strategy_registry, config)

    coordinator.restore_into_view_model(_INTERVALS)

    assert view_model.selectedStrategyKey == TEST_STRATEGY_KEY
    dispatcher.dispatch.assert_not_called()


def test_picking_a_strategy_rebuilds_the_form_but_does_not_arm(
    view_model, dispatcher, strategy_registry
):
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)
    coordinator.restore_into_view_model(_INTERVALS)
    dispatcher.dispatch.reset_mock()

    view_model.requestStrategySelection(TEST_STRATEGY_KEY)
    coordinator.refresh_params_rows()

    assert view_model.botParamsRows != []
    dispatcher.dispatch.assert_not_called()


def test_arming_dispatches_the_command_with_what_the_card_shows(
    view_model, dispatcher, strategy_registry
):
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)
    coordinator.restore_into_view_model(_INTERVALS)
    view_model.requestIntervalSelection("1h")
    view_model.requestSizingPercent(12.5)
    view_model.requestLeverage(4.0)

    coordinator.arm()

    command = dispatcher.dispatch.call_args.args[0]
    assert isinstance(command, ArmStrategyCommand)
    assert command.config == LiveStrategyConfig(
        strategy_key=TEST_STRATEGY_KEY,
        symbol="BTCUSDT",
        interval="1h",
        sizing_percent=12.5,
        leverage=4.0,
    )


def test_a_successful_arm_persists_every_field_and_saves_once(
    view_model, dispatcher, strategy_registry
):
    config = _FakeConfig()
    coordinator = _coordinator(view_model, dispatcher, strategy_registry, config)
    coordinator.restore_into_view_model(_INTERVALS)
    view_model.requestIntervalSelection("1m")
    coordinator.apply_params({"fast_period": "9", "slow_period": "21"})

    coordinator.arm()

    assert (
        config.values[ConfigKeys.TRADING_LIVE_STRATEGY_KEY.value] == TEST_STRATEGY_KEY
    )
    assert config.values[ConfigKeys.TRADING_LIVE_INTERVAL.value] == "1m"
    assert config.values[ConfigKeys.TRADING_LIVE_SYMBOL.value] == "BTCUSDT"
    assert json.loads(config.values[ConfigKeys.TRADING_LIVE_STRATEGY_PARAMS.value]) == {
        "fast_period": 9,
        "slow_period": 21,
    }
    assert config.save_count == 1


def test_a_refused_arm_persists_nothing(view_model, dispatcher, strategy_registry):
    """A configuration the strategy rejected is not one to reload next
    session — `_arm_from_config` would fail the same way at boot, with
    nobody around to read the message."""
    config = _FakeConfig()
    dispatcher.dispatch.return_value = ArmStrategyResult(
        armed=False, block_reason=ArmStrategyBlockReason.TRADING_IS_ENABLED
    )
    coordinator = _coordinator(view_model, dispatcher, strategy_registry, config)
    coordinator.restore_into_view_model(_INTERVALS)

    coordinator.arm()

    assert config.values == {}
    assert config.save_count == 0


def test_invalid_parameters_are_reported_and_not_kept(
    view_model, dispatcher, strategy_registry
):
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)
    coordinator.restore_into_view_model(_INTERVALS)

    accepted = coordinator.apply_params({"fast_period": "not a number"})

    assert accepted is False
    assert view_model.botParamsError != ""
    assert coordinator.build_config().strategy_params == {}


def test_disarm_dispatches_the_disarm_command(
    view_model, dispatcher, strategy_registry
):
    dispatcher.dispatch.return_value = DisarmStrategyResult(disarmed=True)
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)
    coordinator.restore_into_view_model(_INTERVALS)

    result = coordinator.disarm()

    assert isinstance(dispatcher.dispatch.call_args.args[0], DisarmStrategyCommand)
    assert result.disarmed is True


def test_a_blocked_disarm_is_reported_not_swallowed(
    view_model, dispatcher, strategy_registry
):
    dispatcher.dispatch.return_value = DisarmStrategyResult(
        disarmed=False, block_reason=DisarmStrategyBlockReason.TRADING_IS_ENABLED
    )
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)

    result = coordinator.disarm()

    assert result.disarmed is False
    assert result.block_reason is DisarmStrategyBlockReason.TRADING_IS_ENABLED


def test_the_armed_summary_distinguishes_two_armings_of_one_strategy(
    view_model, dispatcher, strategy_registry
):
    """Two runs of the same strategy with different periods are different
    bots; a summary that could not tell them apart would be the same kind
    of half-truth this epic removed from the toggle."""
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)
    fast = LiveStrategyConfig(
        strategy_key=TEST_STRATEGY_KEY,
        symbol="BTCUSDT",
        interval="1m",
        strategy_params={"fast_period": 5},
    )
    slow = LiveStrategyConfig(
        strategy_key=TEST_STRATEGY_KEY,
        symbol="BTCUSDT",
        interval="1m",
        strategy_params={"fast_period": 50},
    )

    assert coordinator.armed_summary(fast) != coordinator.armed_summary(slow)
    assert coordinator.armed_summary(None) == ""


def test_humanized_labels_never_replace_the_registry_key(
    view_model, dispatcher, strategy_registry
):
    """The combo shows a label but must arm by key — deriving one from the
    other by string surgery is how a renamed strategy stops being
    armable."""
    coordinator = _coordinator(view_model, dispatcher, strategy_registry)
    coordinator.restore_into_view_model(_INTERVALS)

    options = view_model.strategyOptions

    assert options[0]["key"] == TEST_STRATEGY_KEY
    assert options[0]["label"] == humanize_strategy_key(TEST_STRATEGY_KEY)
    assert options[0]["label"] != options[0]["key"]


# ---------------------------------------------------------------------- #
# `BUG-107` — the "Nạp chiến lược" button itself.
#
# Everything above drives `arm()`/`disarm()`, the two methods BELOW the
# button. `on_arm_clicked()` — what the button is actually wired to —
# had no test at all, and shipped a call to a tracker method that has
# never existed (`start_action`), so every real click raised
# `AttributeError` before reaching a single line of the logic the tests
# above cover. These call the button handler, not its inside.
# ---------------------------------------------------------------------- #


def test_the_arm_button_dispatches_and_reports_success(
    view_model, dispatcher, strategy_registry
):
    """`BUG-107` — a real click, end to end through the handler."""
    armed = LiveStrategyConfig(
        strategy_key=TEST_STRATEGY_KEY, symbol="BTCUSDT", interval="1m"
    )
    status: list[tuple[str, bool]] = []
    coordinator = _coordinator(
        view_model, dispatcher, strategy_registry, armed=armed, status_sink=status
    )
    coordinator.restore_into_view_model(_INTERVALS)

    coordinator.on_arm_clicked()

    assert isinstance(dispatcher.dispatch.call_args.args[0], ArmStrategyCommand)
    assert status[-1] == (
        f"Đã nạp chiến lược: {coordinator.armed_summary(armed)}",
        False,
    )


def test_the_arm_button_registers_its_action_with_the_presenters_tracker(
    view_model, dispatcher, strategy_registry
):
    """Positive proof the ownership mechanism ran, not merely that no
    exception escaped: the Presenter's tracker must come back holding
    this click's action, under the kind the Presenter handed in, with a
    terminal outcome (`bug-fix-rule.md` §2, `async-ui-action-rule.md` §1).
    """
    tracker: ActionOwnershipTracker[str, None, None] = ActionOwnershipTracker()
    coordinator = _coordinator(
        view_model, dispatcher, strategy_registry, tracker=tracker
    )
    coordinator.restore_into_view_model(_INTERVALS)

    coordinator.on_arm_clicked()

    assert tracker.active_action is not None
    assert tracker.active_action.kind == _ARM_ACTION
    assert tracker.active_outcome is ActionOutcome.SUCCEEDED


def test_a_refused_arm_leaves_the_action_failed_and_says_why(
    view_model, dispatcher, strategy_registry
):
    """A refusal is a finished action, not a stuck PENDING one — a tracker
    left PENDING fences the NEXT click out as a stale/superseded action."""
    dispatcher.dispatch.return_value = ArmStrategyResult(
        armed=False, block_reason=ArmStrategyBlockReason.TRADING_IS_ENABLED
    )
    tracker: ActionOwnershipTracker[str, None, None] = ActionOwnershipTracker()
    status: list[tuple[str, bool]] = []
    coordinator = _coordinator(
        view_model,
        dispatcher,
        strategy_registry,
        tracker=tracker,
        status_sink=status,
    )
    coordinator.restore_into_view_model(_INTERVALS)

    coordinator.on_arm_clicked()

    assert tracker.active_outcome is ActionOutcome.FAILED
    assert status[-1] == (
        ARM_BLOCK_MESSAGES[ArmStrategyBlockReason.TRADING_IS_ENABLED],
        True,
    )


def test_an_arm_that_raises_is_reported_and_finishes_its_action(
    view_model, dispatcher, strategy_registry
):
    """The button's own `except` branch — it also calls `finish_action`,
    so it fails the same way if the tracker's API is wrong."""
    dispatcher.dispatch.side_effect = RuntimeError("sàn từ chối")
    tracker: ActionOwnershipTracker[str, None, None] = ActionOwnershipTracker()
    status: list[tuple[str, bool]] = []
    coordinator = _coordinator(
        view_model,
        dispatcher,
        strategy_registry,
        tracker=tracker,
        status_sink=status,
    )
    coordinator.restore_into_view_model(_INTERVALS)

    coordinator.on_arm_clicked()

    assert tracker.active_outcome is ActionOutcome.FAILED
    assert status[-1] == ("Lỗi khi nạp chiến lược: sàn từ chối", True)


def test_the_presenter_wires_the_arm_signal_to_the_button_handler(
    presenter, mock_dispatcher
):
    """`BUG-107` — the click path itself: `requestArm()` is what the real
    "Nạp chiến lược" button calls, and nothing in this suite had ever
    followed it through `armRequested` -> `_on_arm_requested` ->
    `on_arm_clicked()`. That unfollowed hop is where the crash lived, so
    this walks it on the real ViewModel of a real Presenter.
    """
    mock_dispatcher.dispatch.return_value = ArmStrategyResult(armed=True)

    presenter._view_model.requestArm()

    dispatched = [
        call.args[1] if len(call.args) > 1 else call.args[0]
        for call in mock_dispatcher.dispatch.call_args_list
    ]
    assert any(isinstance(command, ArmStrategyCommand) for command in dispatched)
