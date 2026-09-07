# EPIC-003E3 — `BackTestPresenter.__init__` → `logic/backtest_screen_config.py`

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Nối tiếp:** [`EPIC-003E2`](EPIC-003E2_run_config_builder_logic.md)
**Trạng thái:** ✅ Xong 2026-09-07 · **Rủi ro:** 🟢

---

## 1. Đối tượng

`__init__` của `BackTestPresenter` là **272 dòng** — hàm dài nhất trong cả 3 Presenter quá tải
(Dashboard 282, Data Management 162). Nó là composition root nên **dài là hợp lý**; cái không hợp lý
là 5 lần đọc `IConfig` nằm rải rác trong đó, 3 trong số ấy tự viết thang `try/except` riêng.

## 2. Một lỗi thật, tìm thấy khi gom chúng lại

`bool` là subclass của `int` trong Python, nên `int(True) == 1`:

- `BACKTEST_LOG_MAX_ENTRIES` **có** chặn `isinstance(raw, bool)`.
- `BACKTEST_CHART_KLINES_FETCH_LIMIT` **không**. Đặt key đó thành `true` trong `user_config.json`
  sẽ giới hạn chart còn **1 nến**, không lỗi, không log, không nơi nào báo.

Đây là đúng lớp lỗi mà việc "một cơ chế, một chỗ" tồn tại để chặn: cùng một phép ép kiểu, hai bản
sao, một bản có guard. Giờ cả hai đi qua `_positive_int()` — và `0`/số âm cũng rơi về mặc định thay
vì thành một giới hạn không ai đặt.

**Đây không phải bug người dùng báo**, nên không mở `BUG-*`: không có ai gặp, và nó chỉ với tới được
bằng cách sửa tay file config. Ghi lại ở đây là đủ.

## 3. Đọc tách khỏi áp dụng

`BacktestScreenConfig.read_from(config, …)` trả về một `dataclass(frozen=True)` 7 trường; Presenter
quyết định làm gì với nó. Nhờ vậy câu hỏi *"màn Backtest phụ thuộc những key config nào"* trả lời
được bằng cách đọc **một file**.

`default_interval` **cố ý không** được validate ở đây: `BackTestViewModel` đã có timeframe mặc định
riêng, và một ý kiến thứ hai về "mặc định là gì" chính là bug `EPIC-014` (một `4h` hợp lệ bị bỏ qua
vì cái tuple 5 pill của toolbar đang quyết định giá trị config nào là hợp lệ). Presenter vẫn kiểm nó
bằng `describe_timeframe()` của domain.

## 4. Kết quả

| File | Việc |
| :--- | :--- |
| `.../logic/backtest_screen_config.py` | **Mới** — `BacktestScreenConfig` + `_positive_int()`, mang theo cả comment `BUG-009` và mốc đo 52.147 nến |
| `.../backtest_presenter.py` | 1.828 → **1.776 dòng**; `__init__` 272 → 237 dòng |
| `tests/.../backtest/logic/test_backtest_screen_config.py` | **Mới** — 10 test, gồm `test_true_is_not_a_count_of_one` cho đúng lỗ hổng ở §2 |

**`tests/` diff rỗng tuyệt đối.** `presenter._chart_klines_fetch_limit`,
`presenter._is_dev_mode`, `presenter._log_max_entries` vẫn còn nguyên trên Presenter (2 test hiện có
đọc thẳng chúng) — chỉ nguồn của chúng đổi.

## 5. Còn lại của `__init__` (237 dòng) — chưa làm

Phần lớn còn lại là **wiring thật**: dựng coordinator, nối signal, khôi phục state, dựng chart host.
Đó là việc của composition root, tách tiếp chỉ để hạ số dòng sẽ làm thứ tự khởi tạo (vốn có ràng
buộc thật, xem các comment `EPIC-010F`/`BUG-101`) khó đọc hơn chứ không dễ hơn.
