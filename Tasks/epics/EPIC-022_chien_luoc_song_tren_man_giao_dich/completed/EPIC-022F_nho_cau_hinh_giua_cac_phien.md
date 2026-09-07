# EPIC-022F — Nhớ cấu hình chiến lược giữa các phiên (không tự nạp, không tự bật)

**Status:** ✅ Hoàn thành (2026-09-07) · **Chặn bởi:** D · **Repo:** Elite

---

## 1. Yêu cầu, và cái bẫy đi kèm

`EPIC-021I` §6.2 ghi màn Giao dịch **không có state persistence**. Sau task D, user chọn chiến
lược + 4 thông số mỗi lần mở app là vô lý — cần nhớ.

**Cái bẫy: repo này đã bị đúng lỗi đó 2 lần trong 3 ngày.**

- [`BUG-101`](../../../bug_report/completed/BUG-101_backtest_restore_runs_a_live_chart_preview_on_boot.md)
  — restore form Backtest lúc boot bắn thẳng query thật 200k dòng, vì restore đi qua đúng các
  setter mà user gõ tay.
- [`BUG-104`](../../../bug_report/completed/BUG-104_boot_auto_navigates_into_a_screen_that_starts_live_work.md)
  — nhớ `last_route` + màn Trading tự chạy lúc mở ⇒ mở app lên là live stream tự chạy.

Nên hợp đồng của task này viết bằng phủ định trước:

> Restore **chỉ** đổ giá trị vào ViewModel. Nó **không** gọi `ArmStrategyCommand`, **không** gọi
> `EnableTradingCommand`, **không** chạm mạng. Sau khi mở app, chiến lược luôn ở trạng thái
> **chưa nạp**, giao dịch luôn **TẮT** — user phải tự bấm "Nạp chiến lược" rồi tự bật.

## 2. Thiết kế

Ghi thẳng vào `IConfig` (5 key `trading.live_*` **đã tồn tại**, không thêm key mới) ngay khi user
bấm "Nạp chiến lược" — nạp thành công là mốc duy nhất đáng ghi; các giá trị đang gõ dở không đáng
nhớ. `strategy_params` cần key thứ 6 (`trading.live_strategy_params`, JSON) vì 5 key cũ không có
chỗ chứa thông số.

Ghi rồi `config.save()` theo đúng khuôn `settings_presenter.py:216-222` (`save()` là năng lực của
`ConfigManager`, không thuộc port `IConfig` — phải guard `hasattr`).

Restore: presenter đọc 6 key lúc dựng, đổ vào ViewModel, cờ `_restoring_state = True` bao quanh
để không bắn `armRequested` — cùng cơ chế `BUG-101` đã dùng.

## 3. Đổi theo file

- `config_keys.py` — thêm `TRADING_LIVE_STRATEGY_PARAMS`.
- `app_config.json` — giá trị mặc định `""`.
- `coordinators/strategy_arming_coordinator.py` — ghi/đọc config.
- `trading_presenter.py` — restore lúc dựng, có cờ chặn.

## 4. Test

- Ghi: arm thành công ⇒ 6 key được `set` + `save()` gọi 1 lần.
- Restore: config có sẵn ⇒ ViewModel đúng giá trị, **và** `dispatcher.dispatch` **không** được gọi
  lần nào (chốt hợp đồng phủ định §1), **và** `view_model.enabled is False`.
