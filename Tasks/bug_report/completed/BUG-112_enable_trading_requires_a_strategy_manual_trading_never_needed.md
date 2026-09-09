# BUG-112 — "Bật giao dịch" bắt buộc nạp chiến lược dù người dùng chỉ muốn giao dịch thủ công — vòng luẩn quẩn thật

**Reported date:** 2026-09-09
**Severity:** 🟠 P2 — không crash, nhưng chặn đứng hoàn toàn tính năng giao dịch thủ công
(`EPIC-024B`) cho bất kỳ ai không muốn chạy chiến lược tự động: bật được giao dịch chỉ
sau khi nạp một chiến lược, mà nạp chiến lược đúng symbol muốn giao dịch tay lại bị
chặn tiếp bởi luật khác — deadlock thật.
**Status:** ✅ Đã sửa 2026-09-09 — root-caused, regression-tested, verified.
**Found by:** user tự chạy app thật, mô tả trực tiếp vòng luẩn quẩn kèm log thật.

---

## 1. Symptom

Log + mô tả user gửi trực tiếp:

```
[21:51:09] Lệnh thủ công bị chặn: Giao dịch đang TẮT — bật giao dịch trước khi đặt/huỷ lệnh.
[21:51:18] Chưa nạp chiến lược — chọn chiến lược rồi bấm "Nạp chiến lược" trước.
[21:51:20] Lệnh thủ công bị chặn: Giao dịch đang TẮT — bật giao dịch trước khi đặt/huỷ lệnh.
```

> "logic phản trực giác, tui muốn giao dịch thủ công, thì phải bật giao dịch, mà bật
> giao dịch thì phải nạp chiến lược, giao dịch thủ công thì nạp chiến lược làm gì?"

## 2. Root cause

`EnableTradingCommandHandler` (`EPIC-022B`) chặn "Bật giao dịch" nếu
`LiveStrategySession.is_armed` là `False` — quyết định đúng **tại thời điểm đó**:
"Bật giao dịch" khi ấy chỉ có một nghĩa duy nhất — cho phép chiến lược tự động đặt
lệnh; không nạp gì thì không tick nào sinh ra lệnh, "Bật" mà không làm gì là dối UI
(`domain-truth-rule.md`).

`EPIC-024B` (giao dịch thủ công) đổi nghĩa "Bật giao dịch" thành "tài khoản được phép
gửi lệnh thật" — dùng chung cho **2 caller** độc lập: chiến lược tick VÀ người bấm tay
qua `ExecuteOrderCommand`. `EnableTradingCommandHandler`'s gate cũ không được cập nhật
theo nghĩa mới, nên một người chỉ muốn giao dịch thủ công (không cần chiến lược nào)
vẫn bị bắt nạp một chiến lược chỉ để "mở khoá" nút Bật. Tệ hơn: nếu nạp đúng symbol
muốn giao dịch tay, `PRO-003` §4.1.2 (luật chặn cứng symbol chiến lược đang armed) lập
tức chặn tiếp — người dùng phải nạp chiến lược trên một symbol **khác** hẳn chỉ để mở
khoá, rồi mới giao dịch tay được trên symbol thật muốn dùng. Vòng luẩn quẩn.

Xác minh không có tác dụng phụ khi bỏ điều kiện: `LiveTradingCoordinator` (đường
chiến lược tự động) chỉ nhận `Signal` do `StrategyEngine`/`MarketTickEventHandler`
sinh ra, và cả hai chỉ chạy khi **có** chiến lược đang armed — bỏ gate
`NO_STRATEGY_ARMED` không tạo lại được đúng trạng thái "Bật giao dịch nhưng chiến lược
tự động chạy vô nghĩa" mà `EPIC-022B` từng lo — nó chỉ mở thêm đúng 1 trạng thái hợp
lệ mới: Bật giao dịch + chưa armed + giao dịch thủ công.

## 3. Fix

Bỏ hẳn điều kiện `NO_STRATEGY_ARMED`/tham số `strategy_session: LiveStrategySession`
khỏi `EnableTradingCommandHandler` — "Bật giao dịch" giờ chỉ còn phụ thuộc
`TradingVenue`/kết nối sàn/vị thế bất ngờ, đúng những gì một tài khoản-mức switch cần,
không còn phụ thuộc gì vào chiến lược. Xoá luôn thành viên enum
`EnableTradingBlockReason.NO_STRATEGY_ARMED` (chết) và 2 dòng message tương ứng ở
`dashboard_presenter.py`/`trading_presenter.py`.

**Không đổi** hướng ngược lại: `DisarmStrategyCommandHandler` vẫn từ chối gỡ chiến
lược khi giao dịch đang BẬT (lý do còn lại vẫn đúng — một vị thế mở có thể mất người
quản lý điểm thoát). Sửa comment/docstring liên quan cho khỏi trỏ tới enum đã xoá,
không đổi hành vi đó — nằm ngoài phạm vi báo cáo này, cờ lại cho user quyết định riêng
nếu muốn đối xứng hoá luôn cả hướng đó.

## 4. Regression test

`tests/unit/application/use_cases/trading/test_enable_trading.py::
test_enables_without_any_strategy_armed` (thay thế
`test_blocked_when_no_strategy_is_armed_before_touching_the_network`, hành vi đối
lập trực tiếp) — xác nhận đỏ đúng lý do trước khi sửa (constructor cũ vẫn bắt
`strategy_session`, xoá tham số ở test trước khi sửa handler để mô tả đúng trạng thái
đích), xanh sau khi sửa.

## 5. Xác minh

- `pytest tests/unit/application/use_cases/trading/test_enable_trading.py tests/unit/application/use_cases/trading/test_arm_strategy.py`: 16 passed.
- `pytest tests/sanity/test_composition_root.py tests/unit/presentation/ui/screens/test_dashboard_presenter.py tests/unit/presentation/ui/screens/trading/`: 200 passed — không lùi bước nào ở đường dispatch/DI dùng chung.
- `ruff check`/`ruff format --check` sạch trên mọi file đã sửa.
- `mypy --config-file pyproject.toml` sạch trên các file `application/` đã sửa.
- CI gate đầy đủ (`ci-local.ps1 -Full`) chạy sau khi gộp, xác nhận bằng grep log file thật.
