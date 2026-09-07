"""`EPIC-003F5` — `BackTestViewModel`'s progress bars and run-result
members now forward to `RunProgressViewModel` / `RunResultViewModel`.
This file proves the forwarding; the behaviour is tested directly on the
two sub-ViewModels in `view_models/`.
"""

from __future__ import annotations

from Sagittarius_Elite_Warrior.src.presentation.ui.screens.backtest.backtest_view_model import (
    BackTestViewModel,
)


def test_progress_written_through_the_facade_is_readable_through_it(qapp) -> None:
    vm = BackTestViewModel()

    vm.set_backtest_progress(30.0, "Đang chạy…")
    vm.set_sync_progress(60.0, "Đang tải…")

    assert (vm.backtestProgressPercent, vm.backtestProgressText) == (30.0, "Đang chạy…")
    assert (vm.syncProgressPercent, vm.syncProgressText) == (60.0, "Đang tải…")
    assert vm._run_progress.backtestProgressPercent == 30.0


def test_result_members_forward_to_the_run_result_view_model(qapp) -> None:
    vm = BackTestViewModel()

    vm.set_result("Xong", False)
    vm.set_stat_cards([{"label": "PnL"}], [])
    vm.set_result_warning_text("Thiếu 3 nến")
    vm.set_limitations(["Không mô phỏng funding"])
    vm.set_data_coverage(False, "Chỉ có từ 2024")
    vm.set_needs_data_sync(True)

    assert vm.resultText == vm._run_result.resultText == "Xong"
    assert vm.primaryStatCards == [{"label": "PnL"}]
    assert vm.resultWarningText == "Thiếu 3 nến"
    assert vm.limitations == ["Không mô phỏng funding"]
    assert vm.dataCoverageMessage == "Chỉ có từ 2024"
    assert vm.needsDataSync is True


def test_each_facade_signal_fires_exactly_once_per_change(qapp) -> None:
    """Mutation-verify (`testing-rule.md` §2): adding a manual
    `self.resultChanged.emit()` next to the delegate call in `set_result`
    made this go red (2 `result` entries) — the double-emit defect
    `EPIC-003F1` §3.2 forbids. Reverted before landing."""
    vm = BackTestViewModel()
    seen: list[str] = []
    vm.resultChanged.connect(lambda: seen.append("result"))
    vm.statCardsChanged.connect(lambda: seen.append("cards"))
    vm.limitationsChanged.connect(lambda: seen.append("limits"))
    vm.needsDataSyncChanged.connect(lambda: seen.append("needs_sync"))
    vm.backtestProgressChanged.connect(lambda: seen.append("progress"))

    vm.set_result("Xong", False)
    vm.set_stat_cards([], [])
    vm.set_limitations([])
    vm.set_needs_data_sync(True)
    vm.set_backtest_progress(10.0, "…")

    assert seen == ["result", "cards", "limits", "needs_sync", "progress"]


def test_show_extended_metrics_stays_on_the_facade_across_a_new_run(qapp) -> None:
    """It is a disclosure toggle the user set, not part of the run's
    outcome — clearing the result must not fold it back up."""
    vm = BackTestViewModel()
    vm.showExtendedMetrics = True

    vm.set_result("", False)
    vm.set_stat_cards([], [])

    assert vm.showExtendedMetrics is True


def test_the_extended_metrics_snapshot_round_trips_through_the_facade(qapp) -> None:
    """`MetricsDetailDialogWidget`'s composition root reads this with a
    plain Python call, not a `Property` — a forward that silently returned
    `None` would empty the dialog with no signal and no error."""
    vm = BackTestViewModel()
    marker = object()

    vm.set_extended_metrics_snapshot(marker)

    assert vm.extended_metrics_snapshot() is marker
    assert vm._run_result.extended_metrics_snapshot() is marker
