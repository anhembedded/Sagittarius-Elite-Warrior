"""`EPIC-003F3` — `BackTestViewModel`'s time-range and display-timezone
members are now a facade forwarding to `TimeRangeViewModel`. This file
proves the forwarding; the behaviour itself is tested directly on the
sub-ViewModel in `view_models/test_time_range_view_model.py`.
"""

from __future__ import annotations

from Sagittarius_Elite_Warrior.src.presentation.ui.screens.backtest.backtest_view_model import (
    BackTestViewModel,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.screens.backtest.logic.time_range_preset import (
    TimeRangePreset,
)


def test_writing_the_facade_preset_reaches_the_sub_view_model(qapp) -> None:
    vm = BackTestViewModel()

    vm.timeRangePreset = TimeRangePreset.LAST_30_DAYS.value

    assert vm._time_range.preset == TimeRangePreset.LAST_30_DAYS.value
    assert vm.selectedTimeRangePresetLabel == "30 ngày qua"


def test_writing_the_sub_view_model_is_visible_through_the_facade(qapp) -> None:
    """The other direction matters too: `state_persistence` restores via
    the facade, but a coordinator holding the sub-VM must not be able to
    leave the two disagreeing."""
    vm = BackTestViewModel()

    vm._time_range.customStartText = "2024-01-01 00:00"
    vm._time_range.customEndText = "2024-02-01 00:00"

    assert vm.customStartText == "2024-01-01 00:00"
    assert vm.customEndText == "2024-02-01 00:00"


def test_each_facade_signal_fires_exactly_once_per_change(qapp) -> None:
    """Mutation-verify (`testing-rule.md` §2): adding a manual
    `self.timeRangePresetChanged.emit()` next to the delegate call in
    `_set_time_range_preset` made this go red (2 emits instead of 1) —
    the double-emit class of defect `BUG-042` was, and the one
    `EPIC-003F1` §3.2 forbids re-emitting by hand to avoid. Reverted
    before landing."""
    vm = BackTestViewModel()
    seen: list[str] = []
    vm.timeRangePresetChanged.connect(lambda: seen.append("preset"))
    vm.customStartTextChanged.connect(lambda: seen.append("start"))
    vm.customEndTextChanged.connect(lambda: seen.append("end"))
    vm.displayTimezoneChanged.connect(lambda: seen.append("tz"))

    vm.timeRangePreset = TimeRangePreset.CUSTOM.value
    vm.customStartText = "2024-01-01 00:00"
    vm.customEndText = "2024-02-01 00:00"
    vm.set_display_timezone("Asia/Tokyo")

    assert seen == ["preset", "start", "end", "tz"]


def test_the_option_lists_are_the_sub_view_models_own(qapp) -> None:
    """`backtest_state_fields.py` validates a restored timezone against
    `displayTimezoneOptions` read off the facade — two copies of that list
    is how a value that restores fine in one place gets rejected in the
    other."""
    vm = BackTestViewModel()

    assert vm.timeRangePresetOptions == vm._time_range.presetOptions
    assert vm.displayTimezoneOptions == vm._time_range.displayTimezoneOptions


def test_set_display_timezone_slot_still_updates_the_label(qapp) -> None:
    vm = BackTestViewModel()

    vm.set_display_timezone("Asia/Ho_Chi_Minh")

    assert vm.displayTimezone == "Asia/Ho_Chi_Minh"
    assert vm.displayTimezoneLabel == vm._time_range.displayTimezoneLabel
