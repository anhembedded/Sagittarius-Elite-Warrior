"""`EPIC-003F4` — `BackTestViewModel`'s twelve broker-simulation members
are now a facade forwarding to `BrokerSimViewModel`. This file proves the
forwarding; the clamps and text/value split are tested directly on the
sub-ViewModel in `view_models/test_broker_sim_view_model.py`.
"""

from __future__ import annotations

from Sagittarius_Elite_Warrior.src.presentation.ui.screens.backtest.backtest_view_model import (
    BackTestViewModel,
)


def test_the_slots_the_dialogs_call_reach_the_sub_view_model(qapp) -> None:
    vm = BackTestViewModel()

    vm.set_order_size_text("42")
    vm.set_commission_text("0.02")
    vm.set_pyramiding(4)
    vm.set_slippage_ticks(2)
    vm.set_long_leverage(3.0)
    vm.set_short_leverage(5.0)

    assert vm._broker_sim.orderSizeText == "42"
    assert vm._broker_sim.commissionValue == 0.02
    assert vm._broker_sim.pyramiding == 4
    assert vm._broker_sim.slippageTicks == 2
    assert vm._broker_sim.longLeverage == 3.0
    assert vm._broker_sim.shortLeverage == 5.0


def test_the_clamps_still_apply_when_written_through_the_facade(qapp) -> None:
    """`state_persistence` restores by assigning the facade properties. A
    clamp that only the sub-VM's slots enforce would let a hand-edited
    state file put 0x leverage into a run."""
    vm = BackTestViewModel()

    vm.longLeverage = 0.0
    vm.pyramiding = 0
    vm.commissionValue = -1.0

    assert vm.longLeverage == 1.0
    assert vm.pyramiding == 1
    assert vm.commissionValue == 0.0


def test_each_facade_signal_fires_exactly_once_per_change(qapp) -> None:
    """Mutation-verify (`testing-rule.md` §2): adding a manual
    `self.pyramidingChanged.emit()` next to the delegate call in the
    `set_pyramiding` Slot made this go red (2 `pyramiding` entries) — the
    double-emit defect `EPIC-003F1` §3.2 forbids. Reverted before
    landing."""
    vm = BackTestViewModel()
    seen: list[str] = []
    vm.pyramidingChanged.connect(lambda: seen.append("pyramiding"))
    vm.orderSizeTextChanged.connect(lambda: seen.append("size_text"))
    vm.orderSizeValueChanged.connect(lambda: seen.append("size_value"))
    vm.takeProfitPctEnabledChanged.connect(lambda: seen.append("tp_enabled"))

    vm.set_pyramiding(2)
    vm.set_order_size_text("7")
    vm.takeProfitPctEnabled = True

    assert seen == ["pyramiding", "size_text", "size_value", "tp_enabled"]


def test_reads_come_back_through_the_facade_after_a_sub_view_model_write(
    qapp,
) -> None:
    vm = BackTestViewModel()

    vm._broker_sim.set_commission_type("absolute")
    vm._broker_sim.set_order_size_type("fixed_quantity")

    assert vm.commissionType == "absolute"
    assert vm.orderSizeType == "fixed_quantity"
