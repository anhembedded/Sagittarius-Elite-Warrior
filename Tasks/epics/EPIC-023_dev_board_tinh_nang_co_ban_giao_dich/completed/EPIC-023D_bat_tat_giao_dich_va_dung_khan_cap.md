# EPIC-023D — Bật/Tắt giao dịch + Dừng khẩn cấp + Thống kê phiên trên Dev Board

- **Trạng thái:** ✅ **Đã xong (2026-09-08)** — xem §5 "Kết quả xây dựng".
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

---

## 5. Kết quả xây dựng (2026-09-08)

Đúng thiết kế §2/§3 — không có bug thật/phát sinh khi build lần này (khác `EPIC-023C`): mọi lệnh
`dispatch()` mới viết đều chép nguyên chữ ký 2-đối-số `TradingPresenter`'s own
`_run_enable`/`_run_disable`/`_run_emergency_stop` đã dùng đúng từ đầu, không đi qua đường vòng
1-đối-số `strategy_arming_coordinator.py` từng có.

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/screens/dashboard/dashboard_view_model.py` | Thêm `enabled`/`toggleBusy`/`tradingStateChanged`, `ordersSentThisSession`/`openSymbolsCount`/`sessionStatsChanged`, `toggleRequested`/`emergencyStopRequested` — chép nguyên khối tương ứng của `TradingViewModel` (lý do trùng lặp giống `EPIC-023C`: giới hạn Shiboken, xem `architecture-rule.md` §2.1). |
| `src/presentation/ui/screens/dashboard/dev_board_panel.py` | Nút Bật/Tắt + "DỪNG KHẨN CẤP" thêm vào `header_actions` (Dev Board không có context bar riêng như `TradingView`, nên cả hai cùng đặt cạnh nhau ở header — quyết định thiết kế của task này, không phải sao chép mù). Thêm `_build_session_card()` ("PHIÊN GIAO DỊCH") vào cụm card cuộn. `_sync_armed_summary()` cập nhật để đọc thêm `vm.enabled` — đóng đúng lỗ hổng đã tự ghi chú từ `EPIC-023C` (khi đó `DashboardQmlViewModel` chưa có `enabled`). |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | `self._session_state = container.resolve(TradingSessionState)`; `_toggle_tracker`/`_emergency_stop_tracker` riêng (không dùng chung với `_arm_tracker` hay với Trading — mỗi Presenter tự sở hữu tracker, `async-ui-action-rule.md` §2); seed `set_trading_state(session_state.enabled, False)` + `_refresh_session_stats()` ngay sau khi dựng các tracker. Copy nguyên `_on_toggle_requested`/`_run_enable`/`_run_disable`/`_on_enable_trading_completed`/`_on_disable_trading_completed`/`_on_emergency_stop_requested`/`_run_emergency_stop`/`_on_emergency_stop_completed`/`_apply_emergency_stop_final_state`/`_log_emergency_stop_result`/`_refresh_session_stats` từ `TradingPresenter` — **một khác biệt cố ý**: bỏ hẳn lời gọi `_go_live_if_not_already()` sau một enable thành công, vì Dev Board tự có nút Load History/Start Live/`DEV_BOARD_AUTOSTART_ENABLED` điều khiển độc lập trạng thái live của chart — Bật giao dịch ở đây không được ép chart sang live như một side effect. Mọi `self._view_model.set_status(msg, is_error)` của Trading đổi thành `self._append_log(msg)`, đúng tiền lệ `set_status=lambda message, _is_error: self._append_log(message)` `EPIC-023C` đã chọn cho card Chiến lược (Dev Board không có dòng trạng thái QML riêng). |

### 5.1 Kiểm thử

- **Unit:** 15 test mới trong `test_dashboard_presenter.py` — construction phản ánh
  `TradingSessionState` (kể cả khi đã Bật từ trước), toggle submit đúng worker, chặn toggle khi
  Emergency Stop đang chạy (`BUG-089`'s tiền lệ), enable thành công/bị chặn/lỗi dispatcher, disable
  thành công, emergency stop thành công/thất bại một phần/final-state chưa xác nhận (`BUG-093`'s
  tiền lệ), và `_on_order_filled` cập nhật đúng thẻ Phiên giao dịch. Fixture `session_state`
  (`TradingSessionState()` thật — `_refresh_session_stats()` gọi `len(...)`, một `MagicMock` không
  đáp ứng được) thêm vào `mock_container`; sửa luôn `test_boot_wires_the_container_registered_store_
  into_the_view` (container `Mock()` tự dựng riêng của nó) cho cùng lý do.
- **Xác minh bằng mắt:** `SEW_CAPTURE_SCREENSHOTS=... test_capture_screenshots.py::test_capture[dashboard]`
  — nút "Bật giao dịch"/"DỪNG KHẨN CẤP" hiện đúng ở header, không chèn lên các nút cũ (Reload/WS
  status/price ticker); kiểm tra thêm bằng script debug rằng `_lbl_orders_sent`/`_lbl_open_symbols`
  dựng đúng và `header_actions` trả về đủ 5 widget.
- Toàn bộ cổng: `ruff check`/`ruff format --check` sạch, `mypy --config-file pyproject.toml
  --namespace-packages --explicit-package-bases src scripts` — `Success: no issues found in 257
  source files`, `pytest tests/unit/presentation/ui/screens/ tests/integration/presentation/ui/
  tests/unit/presentation/ui/common/` — **1151 passed, 4 skipped**.
