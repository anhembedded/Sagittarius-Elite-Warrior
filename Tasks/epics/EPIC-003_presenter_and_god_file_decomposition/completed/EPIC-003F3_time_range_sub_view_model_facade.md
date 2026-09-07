# EPIC-003F3 — Lát cắt 3 của `003F`: `TimeRangeViewModel` + facade

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Task cha:** [`EPIC-003F`](EPIC-003F_backtest_viewmodel_composite_design_review.md)
**Trạng thái:** ✅ Xong 2026-09-07
**Rủi ro:** 🟡 — đúng khuôn `003F1`/`003F2`, không phát minh gì mới.

---

## 1. Phạm vi

Nhóm "khoảng thời gian" mà `003F1` §7 xếp là lát kế tiếp. Đo lại tại thời điểm làm, không dùng
con số cũ:

| Thành viên | Loại |
| :--- | :--- |
| `timeRangePresetOptions`, `displayTimezoneOptions` | 2 `Property(constant=True)` |
| `timeRangePreset`, `selectedTimeRangePresetLabel`, `customStartText`, `customEndText` | 4 `Property` |
| `displayTimezone`, `displayTimezoneLabel` | 2 `Property` |
| `timeRangePresetChanged`, `customStartTextChanged`, `customEndTextChanged`, `displayTimezoneChanged` | 4 `Signal` |
| `set_display_timezone` | 1 `Slot` |

**Cố tình để lại facade:** `openTimeRangePickerRequested` / `openTimezonePickerRequested` — cùng lý
do `003F2` để lại `openStrategyPickerRequested`: chúng thuộc khối 10 signal "mở modal", kéo 2 cái
ra khỏi khối đó chỉ để khớp tiền tố tên là đánh đổi một tính cố kết lấy một cái tệ hơn.

## 2. Vì sao múi giờ đi cùng khoảng thời gian

Không phải vì tên gần nhau. `preset` + 2 ô `custom*` là **cửa sổ nến nào được chạy**;
`displayTimezone` là **cửa sổ đó được gọi tên theo đồng hồ nào** (`BOT-097`) — cùng một quyết định
của người dùng, và `resolve_time_range()` đọc 3 cái đầu như một cụm. Hai bảng option ở lại cùng chỗ
với 2 thuộc tính label đọc chúng: tách phép tra khỏi bảng bị tra là cách một label bắt đầu nói khác
giá trị nó gán nhãn.

## 3. Kết quả

| File | Việc |
| :--- | :--- |
| `.../view_models/time_range_view_model.py` | **Mới** — 154 dòng, 4 signal / 8 property / 1 slot |
| `.../backtest_view_model.py` | 1.417 → **1.405 dòng**; dựng sub-VM + connect 4 signal, 8 property đổi thành forward; xoá import `TimeRangePreset` và cả cụm `display_timezone_service` không còn dùng trực tiếp |
| `tests/.../view_models/test_time_range_view_model.py` | **Mới** — 7 test thẳng vào sub-VM |
| `tests/.../test_backtest_view_model_time_range_facade.py` | **Mới** — 5 test chứng minh forwarding |

**`tests/` diff rỗng tuyệt đối** (`git diff --name-only tests/` không có dòng nào) — chỉ thêm file
mới. Đúng điều kiện `003F` §4.1: phải sửa test thì facade sai.

### 3.1 Mutation-verify đã làm thật (`testing-rule.md` §2)

Thêm tạm `self.timeRangePresetChanged.emit()` cạnh `self._time_range.preset = value` trong
`_set_time_range_preset` → `test_each_facade_signal_fires_exactly_once_per_change` đỏ đúng như kỳ
vọng (`['preset', 'preset', 'start', …]`) → revert nguyên văn.

### 3.2 Một test của chính tôi sai trước, code đúng

`test_display_timezone_label_is_the_human_name_not_the_tz_id` khẳng định label khác tz id — sai:
`get_display_timezone_label()` **cố ý** trả về chính IANA id cho mọi vùng ngoài `UTC` và khoá "hệ
thống". Đã sửa test để phát biểu đúng hợp đồng thật, không sửa code cho khớp test.
