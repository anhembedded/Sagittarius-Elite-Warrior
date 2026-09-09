# BUG-112 — Cài mới (fresh install): combo khung thời gian trông như đã chọn, nhưng `liveInterval` rỗng khiến "Nạp chiến lược" bị từ chối câm lặng ở lần bấm đầu tiên

**Reported date:** 2026-09-09
**Fixed date:** 2026-09-09
**Severity:** 🟡 P2 — không mất tiền (chưa arm được thì chưa có gì chạy), nhưng chặn đứng hành
động cốt lõi đầu tiên của một user mới, và trông y hệt một nút chết (silent no-op) chứ không
phải một lời từ chối có lý do.
**Status:** ✅ Fixed — xem §3.

---

## 1. Hiện tượng (Symptom)

Phát hiện khi xây `EPIC-023C` (card Chiến lược của Dev Board): test tích hợp mới
`tests/integration/presentation/ui/test_dev_board_known_gaps.py::test_strategy_dropdown_arms_the_selected_strategy`
là test **đầu tiên trong repo** thật sự bấm nút Arm end-to-end qua dispatcher thật với config
store thật **chưa từng lưu gì** (đúng trạng thái một máy cài mới). Test đỏ ngay ở bước arm đầu
tiên, phải né bằng cách tự chọn lại khung thời gian trước khi bấm — đó chính là dấu hiệu của bug
này, không phải lỗi ở test.

Kịch bản thật trên một máy cài mới: user mở màn Giao dịch (hoặc Dev Board) lần đầu, thấy card
Chiến lược đã hiện sẵn một khung thời gian ở combo (ví dụ "1m") — **trông như đã chọn xong** — và
bấm thẳng "Nạp chiến lược" mà không đụng vào combo đó. Lệnh bị từ chối với lý do
`ArmStrategyBlockReason.MISSING_SYMBOL_OR_INTERVAL` ("Cần chọn cả symbol và khung thời gian giao
dịch") dù màn hình rõ ràng đang hiện một khung thời gian.

## 2. Root cause

`LiveStrategyConfigStore.load()`
(`src/application/services/live_strategy_config_store.py:44-64`) đọc key
`ConfigKeys.TRADING_LIVE_INTERVAL` bằng `_text()`, mặc định `""` khi key chưa từng tồn tại — đúng
trạng thái của một `IConfig` chưa lưu gì.

`StrategyArmingCoordinator.restore_into_view_model()`
(`src/presentation/ui/common/strategy_arming_coordinator.py`, trước fix ở dòng ~210) truyền thẳng
`saved.interval` (`""`) vào `view_model.set_strategy_selection(...)` mà không có bước dự phòng nào
— khác hẳn `saved_key` ngay phía trên, vốn **đã có sẵn** fallback về `available[0]` khi key đã lưu
không còn tồn tại trong registry, nhưng interval thì chưa từng có fallback tương đương.

Ở tầng UI, cả `trading_view.py` (panel/card sync) lẫn
`dev_board_panel.py::_sync_strategy_selection()` chỉ set combo một cách tường minh khi giá trị là
truthy:

```python
if vm.liveInterval:
    self._cbo_live_interval.setCurrentText(vm.liveInterval)
```

Khi `vm.liveInterval == ""`, khối này không chạy — nhưng combo đã được đổ danh sách khung thời
gian vài dòng trước đó qua `_sync_strategy_options()` (gọi `addItems(...)` dưới `blockSignals(True)`),
và hành vi mặc định của `QComboBox.addItems()` là tự chọn index 0 ngay khi có item — **im lặng**,
vì đang ở trong `blockSignals`, nên `currentTextChanged` không bắn và `view_model.liveInterval`
không bao giờ được cập nhật theo. Kết quả: combo **nhìn thấy** đã chọn "1m", nhưng
`view_model.liveInterval` vẫn là `""`. `StrategyArmingCoordinator.build_config()` đọc thẳng
`self._view_model.liveInterval` để dựng `LiveStrategyConfig(interval="")`, và
`ArmStrategyCommand` từ chối đúng như thiết kế — refusal đúng, nhưng vì lý do UI chưa bao giờ nói
cho user biết.

Bug này nằm ở `StrategyArmingCoordinator` dùng chung, nên ảnh hưởng **cả 2 màn** dùng chung
Coordinator này (Giao dịch và Dev Board) — chỉ chưa từng lộ ra vì chưa có test nào đi qua đúng
đường "config store thật, chưa từng lưu, bấm Arm thật" trước `EPIC-023C`.

## 3. Fix

`restore_into_view_model()` giờ dự phòng cho `interval` giống hệt cách `strategy_key` đã làm:
khi `saved.interval` rỗng và `interval_options` không rỗng, dùng `interval_options[0]` — đúng
phần tử mà `QComboBox.addItems()` sẽ tự chọn trên thực tế. Nhờ vậy `view_model.liveInterval` luôn
khớp với những gì combo box đang hiển thị ngay sau khi restore, và `build_config()` không còn bao
giờ dựng một `LiveStrategyConfig` với `interval=""` trong khi combo trông như đã có lựa chọn.

Sửa đúng 1 chỗ (`StrategyArmingCoordinator`, dùng chung cho cả 2 màn) — không đụng
`trading_view.py` hay `dev_board_panel.py`.

## 4. Regression test

`tests/unit/presentation/ui/common/test_strategy_arming_coordinator.py::test_a_fresh_unsaved_store_falls_back_to_the_first_interval`
— dựng coordinator với `_FakeConfig()` rỗng (đúng trạng thái cài mới), gọi
`restore_into_view_model(_INTERVALS)`, assert `view_model.liveInterval == _INTERVALS[0]` và
`coordinator.build_config().interval == _INTERVALS[0]`.

Xác nhận test **fail đúng lý do** trước khi sửa (`AssertionError: assert '' == '1m'`, tạm bỏ đoạn
fallback bằng `git stash` để chạy lại), rồi xanh sau khi áp fix. Giữ lại vĩnh viễn theo
`bug-fix-rule.md` §4.

## 5. Kiểm chứng

`pwsh -NoProfile -File scripts/ci-local.ps1 -Full` (môi trường Linux, bootstrap mới: venv Python
3.12, PowerShell 7.5.0, `requirements.txt`, `sagittarius_engine` từ GitHub, thư viện hệ thống Qt
offscreen) — **PASS**: 3877 passed, 4 skipped, coverage 94.72% (ngưỡng 80%), Sanity xanh, log
scan không có dòng `WARNING|ERROR|CRITICAL` nào. Đã đọc trực tiếp file log thật
(`logs/ci-local-20260909-121359.log`), không chỉ tin console output.
