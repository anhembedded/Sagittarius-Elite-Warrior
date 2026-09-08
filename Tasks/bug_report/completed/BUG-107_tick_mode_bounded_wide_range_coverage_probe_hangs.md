# BUG-107 — Realtime/tick mode + a *bounded* but very wide range (e.g. "365 ngày qua") hangs the Run Backtest coverage probe with no progress bar

**Reported date:** 2026-09-08
**Severity:** 🟠 P1 — clicking "Chạy Backtest" in Realtime (tick) mode with
a wide preset (observed: "365 ngày qua") makes the app appear frozen for
minutes, with no progress indicator at all — same user-visible symptom
class as `BUG-073`, different trigger.
**Status:** ✅ Đã sửa 2026-09-08 — root-caused, regression-tested,
verified.
**Found by:** user pasted a real INFO-level session log and described the
symptom directly ("no bị đứng rồi" / "đứng lâu mà ko thấy hiện thanh
process gì").

---

## 1. Symptom

Real session log (trimmed to the relevant lines; full log supplied by user
in chat, not attached as a file):

```
16:01:00,783 - App.BackTestPresenter - INFO - [backtest-config] execution mode set to HISTORICAL_TICK
16:01:14,025 - App - INFO - Executing query: GetHistoricalKlinesQuery
16:01:14,026 - App.QueryHandler - INFO - BACKTEST_TRACE action=query_execute_start symbol='ETHUSDT' timeframe='15m' limit=200000 start=datetime.datetime(2025, 9, 2, 10, 20, tzinfo=datetime.timezone.utc) end=datetime.datetime(2026, 9, 1, 23, 59, tzinfo=datetime.timezone.utc) order_by_desc=True
16:01:14,378 - App.QueryHandler - INFO - BACKTEST_TRACE action=query_execute_complete symbol='ETHUSDT' rows=6305
16:01:14,378 - App - INFO - Executing query: GetBacktestRangeCoverageQuery
16:01:14,486 - App.ChartCard - INFO - [chart-data] ChartCard(ETHUSDT): loaded 6305 candles ...
16:01:17,289 - App - INFO - Executing query: GetBacktestRangeCoverageQuery
```

— log ends there. User confirmed directly: no progress bar of any kind
appeared while it sat like this; earlier chart data had already loaded
successfully, so the freeze is specifically at this second coverage query.
`start`/`end` (2025-09-02 → 2026-09-01) is a 364-day window — the app's
standard "365 ngày qua" preset, not a hand-typed custom range.

## 2. Root cause

`BackTestPresenter`'s "Chạy Backtest" flow calls
`ExecutionCoordinator._coverage_is_ready()`
(`src/presentation/ui/screens/backtest/coordinators/execution_coordinator.py:182-190`),
which calls `self._probe_coverage(config)` →
`DataSyncCoordinator.probe_coverage()`
(`coordinators/data_sync_coordinator.py:114-123`) **synchronously on a
background thread, with no progress reporting of its own** — this is the
"no progress bar" the user describes; unlike `SyncMarketDataCommand`,
which has one, `GetBacktestRangeCoverageQuery` never reports intermediate
progress.

`probe_coverage()` dispatches `GetBacktestRangeCoverageQuery` at
`effective_data_interval(config)`
(`coordinators/execution_coordinator.py:100-111`), which returns
`config.tick_resolution` (**1 second**, BOT-075's default) whenever
`execution_mode == HISTORICAL_TICK` — **regardless of the chart's own
display timeframe** (`15m` in the log above; that is only what
`GetHistoricalKlinesQuery`/the chart preview use). So the coverage probe
runs its `LAG(...) OVER (ORDER BY open_time ASC)` window-function query
(`sqlalchemy_repository.py::get_range_coverage()`) at **1-second
granularity across a 364-day window**.

`Tasks/reports/tick_data_feasibility.md` §3.2/§3.3 (BOT-075's own
validated spike) measured a single **7-day**/1s coverage probe (query +
handler) at **~17 seconds** and concluded it is "not usable synchronously
— MUST run in background + progress + cancel". This exact code path runs
in the background, but has **no progress** and **no cancellation**
(`GetBacktestRangeCoverageQueryHandler.execute()` takes no cancellation
token at all — the same finding `BUG-073` already made about this query
type). A 364-day window is **52×** wider than the already-borderline
7-day baseline.

`TickModeRequiresBoundedRangeRule`
(`src/presentation/ui/screens/backtest/logic/pre_backtest_assertions.py`,
added by `BUG-073`) was supposed to be the gate in front of exactly this —
but it only checked `is_unbounded_range` (`start_time is None`, the
"Toàn bộ lịch sử" preset). The "365 ngày qua" preset resolves to a **real**
`start_time`/`end_time` pair (`time_range_preset.py::resolve_time_range()`
— `LAST_365_DAYS` maps to `now - timedelta(days=365)`), so the rule never
fired: **bounded is not the same as cheap**, and the rule only ever
checked the former.

## 3. Fix

Widened `TickModeRequiresBoundedRangeRule` to also reject a *bounded*
tick-mode range wider than `_MAX_TICK_MODE_RANGE_DAYS = 7` — reusing
BOT-075's own already-validated feasible window rather than inventing a
new number. `PreBacktestInput` gained `start_time`/`end_time` fields (the
*resolved* range, not raw preset/text) so the rule can compute the span;
`run_config_builder.py::build_run_config()` now resolves
`start_time`/`end_time` **before** running the assertion pipeline (a pure
reordering of existing calls — `resolve_time_range()` has no dependency on
the assertion result) instead of after, so the Run-button path is checked
for real. The check is expressed once, as a plain function
(`tick_mode_range_too_wide()`), so `ChartPreviewCoordinator.request_preview()`
(the automatic toolbar-change preview `BUG-073` already guarded for the
unbounded case) can reuse the identical threshold rather than re-deriving
it — that coordinator's own coverage dispatch has the same
no-progress/no-cancellation shape.

The achievable, verifiable fix is the same one `BUG-073` already
established: refuse to dispatch the hazardous query shape at all. Adding
real cancellation/timeout to `GetBacktestRangeCoverageQueryHandler`/
`get_range_coverage()` would need a `sagittarius_engine`-level capability
this repo does not have — out of scope here, same as `BUG-073`'s own
conclusion.

## 4. Regression test

- `tests/unit/presentation/ui/screens/test_pre_backtest_assertions.py` —
  5 new tests on the pure rule: unbounded-range rejection (pre-existing
  `BUG-073` behavior, previously untested at all), at-the-7-day-limit
  accepted, 364-day bounded range rejected (**fails before the fix**:
  `assert 0 == 1`, no issue raised), a wide range outside tick mode still
  accepted, a still-resolving transient state (`end_time=None`) not
  false-rejected.
- `tests/unit/presentation/ui/screens/backtest/logic/test_run_config_builder.py` —
  3 new tests proving the end-to-end wiring, not just the isolated rule:
  the "365 ngày qua" preset in tick mode is refused with a message naming
  "7 ngày", the "7 ngày qua" preset in tick mode still runs, and the same
  365-day preset outside tick mode still runs.
- `tests/unit/presentation/ui/screens/backtest/coordinators/test_chart_preview_coordinator.py` —
  3 new tests mirroring the same 3 cases for the automatic toolbar preview
  path.

All new tests confirmed to fail for the right reason before the fix (the
pure-rule test asserted directly; the two integration test files' behavior
follows deterministically from the same underlying rule, verified by
running the pure-rule test red first).

## 5. Xác minh

- `mypy --config-file pyproject.toml --namespace-packages --explicit-package-bases src scripts`:
  `Success: no issues found in 257 source files`.
- `ruff check`/`ruff format --check` trên các file đổi: sạch.
- `pytest tests/unit/presentation/ui/screens/test_pre_backtest_assertions.py tests/unit/presentation/ui/screens/backtest/logic/test_run_config_builder.py tests/unit/presentation/ui/screens/backtest/coordinators/test_chart_preview_coordinator.py`:
  **40 passed**.
- `pytest tests/unit/`: **3650 passed** (11 new, không lùi bước nào).
- `pytest tests/integration/`: **108 passed, 4 skipped** (skip có sẵn từ
  trước, không liên quan).
- `pytest tests/sanity/`: **26 passed**.

## 6. Vì sao lỗ hổng test cũ không bắt được (câu hỏi user đặt ra trực tiếp)

`TickModeRequiresBoundedRangeRule` (viết ở `BUG-073`) **chưa từng có test
riêng nào** trước bug này —
`tests/unit/presentation/ui/screens/test_pre_backtest_assertions.py` chỉ
có 7 test, toàn bộ về `capital`/`custom range` text, không test nào set
`is_tick_mode=True`. `ChartPreviewCoordinator`'s guard (cũng từ `BUG-073`)
có test, nhưng đó là một guard KHÁC (tự động lúc đổi toolbar), không phải
đường "Chạy Backtest" thật sự đi qua `run_config_builder.py`. Kết quả:
lớp lỗi `BUG-073` đã "vá" trên giấy nhưng cây gọi chính (Run button) chưa
từng bị test chạm tới nửa kia của hazard (bounded-nhưng-quá-rộng) — sanity
tier không phải chỗ đúng để bắt lỗi logic-nghiệp-vụ kiểu này (nó không
mô phỏng "user chọn preset 365 ngày + tick mode rồi bấm Run"); đây đúng
nghĩa là lỗ hổng ở tầng unit test của riêng rule này, không phải sanity
thiếu.
