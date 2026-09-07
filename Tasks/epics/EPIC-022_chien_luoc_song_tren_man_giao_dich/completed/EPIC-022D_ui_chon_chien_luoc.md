# EPIC-022D — UI: card CHIẾN LƯỢC + dialog Thông số Chiến lược trên màn Giao dịch

**Status:** ✅ Hoàn thành (2026-09-07) · **Chặn bởi:** A, B, C · **Repo:** Elite

---

## 1. Thiết kế UI

Rail phải của màn Giao dịch hiện trả về **đúng 1 `Card`** (`trading_view.py:288-307`). Đổi thành
`QWidget` + `QVBoxLayout` chứa nhiều card, theo thứ tự đọc từ trên xuống:

```
┌ CHIẾN LƯỢC ─────────────────────┐
│ Chiến lược   [EMA Crossover ▾]  │
│ Khung TG     [1m ▾]             │
│ % vốn/lệnh   [20.0 ⇅]           │
│ Đòn bẩy      [1.0 ⇅]            │
│ [ Thông số Chiến lược… ]        │
│ [ Nạp chiến lược ]  [ Gỡ ]      │
│ Đang nạp: EMA Crossover 12/26   │
└─────────────────────────────────┘
┌ TÍN HIỆU GẦN NHẤT ──────────────┐   ← task E
┌ PHIÊN GIAO DỊCH ────────────────┐   ← đã có
```

- Nút **Nạp chiến lược** = `ArmStrategyCommand`; **Gỡ** = `DisarmStrategyCommand`. Nạp là hành
  động rõ ràng của user, **không** tự nạp khi vừa đổi combobox — đổi combobox mà tự dựng lại engine
  là đúng loại tác dụng phụ ngầm `BUG-101` đã phải sửa ở màn Backtest.
- Cả cụm `setEnabled(False)` khi trading đang BẬT (rào 4.1 của epic) — chặn bằng UI **và** bằng
  command, không chỉ một trong hai.
- Thuật ngữ bắt buộc: **"Thông số Chiến lược"** (`ui-presentation-rule.md`).

Dialog thông số: `Overlay` dùng lại `bot_params_form` + `param_field` vừa thăng cấp ở task C,
theo khuôn `StrategyPropertiesDialog` nhưng chỉ 1 tab (Backtest có 4 tab vì còn broker properties
— màn Giao dịch không có khái niệm đó, sizing/leverage đã nằm ngay trên card).

## 2. Đổi theo file

- `trading_view_model.py` — thêm nhóm property/signal chiến lược (`strategyOptions`,
  `selectedStrategyKey`, `liveInterval`, `sizingPercent`, `leverage`, `armedSummary`,
  `botParamsRows`, `botParamsError`) + `armRequested`/`disarmRequested`/`botParamsSaveRequested`.
- `trading_view.py` — `_build_rail()` trả nhiều card; thêm `_build_strategy_card()`.
- Mới `screens/trading/trading_strategy_dialog.py` — dialog Thông số Chiến lược.
- Mới `screens/trading/coordinators/strategy_arming_coordinator.py` — giữ params đang soạn, gọi
  2 command, ghi `IConfig`. Presenter đã 729 dòng, thêm thẳng vào là vượt ngưỡng
  `async-ui-action-rule.md` §2.
- `trading_presenter.py` — nối signal, sở hữu `ActionOwnershipTracker` cho action `arm_strategy`
  (Coordinator **không** được tự giữ action-id — §2 cấm rõ).

## 3. Test

`test_trading_strategy_arming.py` (mới) — đổi combobox không tự arm; arm gọi đúng command với
đúng params; trading bật ⇒ cụm control bị khoá; block reason hiện đúng câu tiếng Việt.
`test_trading_view_contract.py` — cập nhật `ITradingView` nếu đổi.
