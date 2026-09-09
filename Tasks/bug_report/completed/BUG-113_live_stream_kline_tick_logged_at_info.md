# BUG-113 — Mỗi tick kline live log ở mức INFO — tái diễn đúng lớp lỗi `BUG-042`/`BUG-095`

**Reported date:** 2026-09-09
**Severity:** 🟡 P3 — không sai dữ liệu, nhưng đúng lớp log per-event ở `INFO` mà
`BUG-042` từng làm treo UI (838 dòng trade), và `BUG-095` đã sửa 4 dòng cùng lớp ở
`futures_user_data_stream.py` — dòng `[Live Stream]` này lọt lưới lúc đó vì nằm ở
file khác (`binance_websocket_service.py`, luồng giá kline chứ không phải User Data
Stream).
**Status:** ✅ Đã sửa 2026-09-09 — root-caused, regression-tested, verified.
**Found by:** user đọc log thật của chính mình, chỉ đúng lý do ("log này xuất hiện
không đúng log level, nó không nên ở INFO level") mà không cần mình chỉ trước.

---

## 1. Symptom

Log thật user gửi (trích, đầy đủ hơn trong log gốc):

```
2026-09-09 22:26:02,516 - App.LiveStream - INFO - [Live Stream] ETHUSDT | Price: 2474.48 | Vol: 0.0474 | Closed: False
2026-09-09 22:26:04,295 - App.LiveStream - INFO - [Live Stream] ETHUSDT | Price: 2474.47 | Vol: 0.0979 | Closed: False
2026-09-09 22:26:06,302 - App.LiveStream - INFO - [Live Stream] ETHUSDT | Price: 2474.47 | Vol: 0.1059 | Closed: False
...
```

Một dòng cho **mỗi** message kline WebSocket nhận được — trên một symbol đang hoạt
động, đây là nhiều dòng mỗi giây, không phải một quyết định/một lần chuyển trạng
thái.

## 2. Root cause

`BinanceWebsocketService._process_socket_message()`
(`src/infrastructure/binance/binance_websocket_service.py:241`, trước sửa) gọi
`logger.info(...)` cho **mọi** message kline nhận từ WebSocket — đúng lớp lỗi
`logging-rule.md` §4 ("Summarise per gesture or per operation — never per event")
và §6 (`INFO` dành cho quyết định/tóm tắt, `DEBUG` cho chi tiết per-event) cấm, và
đúng cơ chế `BUG-042` đã làm treo UI (`SignalLogHandler` mirror mọi dòng `App.*`
`INFO+` qua Qt signal có hàng đợi — 838 dòng per-trade lúc đó đủ để đơ UI thread).

`BUG-095` (2026-09-03) đã sửa đúng lớp lỗi này cho 4 dòng ở
`futures_user_data_stream.py` (`ACCOUNT_UPDATE`/`ORDER_TRADE_UPDATE`), nhưng dòng
`[Live Stream]` này sống ở một file khác hẳn — luồng giá kline
(`BinanceWebsocketService`), không phải luồng tài khoản (`FuturesUserDataStream`) —
nên không nằm trong phạm vi rà soát của `BUG-095`.

## 3. Fix

Đổi `logger.info(...)` → `logger.debug(...)` tại đúng dòng đó, giữ nguyên nội dung
message (chỉ đổi sang lazy `%s` formatting thay f-string, tránh format string khi
DEBUG đang tắt — cùng convention `_handle_order_trade_update()` đã dùng).

## 4. Regression test

`tests/unit/infrastructure/binance/test_binance_websocket_service.py::
test_kline_tick_logs_at_debug_not_info` — xác nhận đỏ đúng lý do trước khi sửa
(`caplog` bắt được dòng ở `INFO`, không phải `DEBUG`), xanh sau khi sửa. Cùng
khuôn mẫu 3 test `BUG-095` đã viết cho `test_futures_user_data_stream.py`.

## 5. Xác minh

- `pytest tests/unit/infrastructure/binance/test_binance_websocket_service.py`: 17 passed.
- `ruff check`/`ruff format --check` sạch trên 2 file đã sửa.
- `mypy --config-file pyproject.toml` sạch trên file `src/` đã sửa.
- CI gate đầy đủ (`ci-local.ps1 -Full`) chạy sau khi gộp, xác nhận bằng grep log file thật.
