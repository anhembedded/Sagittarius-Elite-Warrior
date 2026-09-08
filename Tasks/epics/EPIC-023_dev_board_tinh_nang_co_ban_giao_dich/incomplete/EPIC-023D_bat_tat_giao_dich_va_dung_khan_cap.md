# EPIC-023D — Bật/Tắt giao dịch + Dừng khẩn cấp + Thống kê phiên trên Dev Board

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** `EPIC-023A`, `EPIC-023C` (cần bảng Vị thế/Lệnh chờ + card Chiến lược đã có để bật
  giao dịch có gì mà xem) · **Chặn:** —

**Rủi ro cao nhất trong epic — hành động ảnh hưởng thật tới tài khoản testnet.** Làm sau cùng,
soát kỹ nhất, review kỹ trước khi merge.

## 1. Việc cần làm

Thêm nút Bật/Tắt giao dịch (header, giống `TradingView`'s `_toggle_button`) + Dừng khẩn cấp
(context bar) + card "Phiên giao dịch" (số lệnh đã gửi, số symbol có vị thế mở) vào Dev Board.

## 2. Thay đổi theo file

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/screens/dashboard/dashboard_view_model.py` | Thêm `enabled`/`toggleBusy`/`tradingStateChanged`, `ordersSentThisSession`/`openSymbolsCount`/`sessionStatsChanged` — khớp `TradingViewModel`'s property tương ứng. |
| `src/presentation/ui/screens/dashboard/dev_board_panel.py` | Nút Bật/Tắt (header_actions), nút Dừng khẩn cấp, card Phiên giao dịch — bố cục giống `trading_view.py`. |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | `self._session_state = container.resolve(TradingSessionState)` (singleton, đọc trạng thái Bật/Tắt hiện tại — có thể đã Bật từ màn Trading); `_toggle_tracker`/`_emergency_stop_tracker` riêng (không dùng chung với Trading — mỗi Presenter tự sở hữu tracker); copy nguyên `_on_toggle_requested`/`_on_emergency_stop_requested`/`_on_enable_trading_completed`/`_on_disable_trading_completed`/`_on_emergency_stop_completed` từ `trading_presenter.py` — cùng thuật toán. |

## 3. Quyết định thiết kế

- **Không tạo "trạng thái Bật/Tắt riêng của Dev Board".** `enabled` đọc từ
  `TradingSessionState.enabled` (singleton) lúc dựng Presenter — nếu Trading đã Bật trước đó, Dev
  Board mở lên phải hiện đúng "đang Bật", không phải "Tắt" mặc định.
- **Mỗi Presenter tự có `ActionOwnershipTracker` riêng** (`async-ui-action-rule.md` §2 — tracker
  không phải trạng thái chia sẻ, chỉ chống double-submit trong nội bộ một Presenter). Hai màn cùng
  bấm Bật thì cả hai request đều tới `EnableTradingCommand` thật — command handler tự chịu trách
  nhiệm idempotent/chặn theo `TradingSessionState`, không phải việc của tracker.

## 4. Kiểm thử

Cùng khuôn `test_trading_presenter.py`'s phần toggle/emergency-stop/session-stats, viết bản Dev
Board. Bổ sung 1 test riêng: dựng `DashboardPresenter` khi `TradingSessionState.enabled == True`
sẵn (giả lập đã Bật từ màn Trading trước đó) → ViewModel phải seed `enabled=True`, không phải
`False`. Không sanity mới.
