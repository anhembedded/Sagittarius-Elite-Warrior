# EPIC-025B — Phase 1: `modules/trading`; Trading + Dev Board thành composition surface

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** A · **Chặn:** C
- **Đọc trước:** HLD §3.3 (contracts `trading`), §4.2 (surface Trading / Dev Board, `dev_probe`);
  ADR D4, D12. **Rủi ro cao nhất epic**: `TradingSessionState` là state mutable dùng chung bởi 3
  Presenter + 3 handler + thread websocket.

## 1. Việc cần làm

1. `modules/trading/`: `domain/trading` hiện có, `use_cases/trading` (trừ arm/disarm — về `strategy`
   ở Phase 2, tạm giữ với allowlist), `infrastructure/binance` phần trading REST + user-data stream,
   credentials, `PositionRefreshService` (`BUG-117`) — `trading` **sở hữu** read-model vị thế.
2. `contracts/`: `IOrderSubmission`, `IOpenPositions`, `ITradingSessionQuery`, DTO
   (`PositionSnapshot`, `OpenOrderSnapshot`, `TradingSessionSnapshot`), event `OrderFilled`,
   `PositionChanged`, `PositionClosed`, `TradingSessionChanged`.
3. Widget góp: positions table, open orders table, manual order card, session control (Bật/Tắt/
   Emergency stop), account/equity — **một** bản mỗi thứ, có wrapper Python trong `modules/trading/ui/`.
4. `screens/trading` và `screens/dashboard` → `surfaces/trading/`, `surfaces/dev_board/`: chỉ layout
   + đăng ký widget theo contribution; **0 logic nghiệp vụ**. Dev Board gate `dev.mode`; treo
   `dev_probe` (probe đầu tiên: "exchange API tester" của `trading` — gọi đúng adapter thật).
5. 9 item `ui/common/` chỉ 2 màn dùng → về `modules/trading` (phần strategy sang Phase 2).

## 2. Xong khi

- Script đếm tên method trùng `trading` ↔ `dashboard`: **59 → 0** (ghi số vào PR).
- User tự chạy Testnet: đặt lệnh tay, huỷ lệnh, Bật/Tắt giao dịch, PnL cập nhật — hành vi y như
  trước (`BUG-112`/`116`/`117` regression test vẫn xanh).
