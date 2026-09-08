# EPIC-023C — Card "Chiến lược" thật (Nạp/Gỡ) + Tín hiệu gần nhất

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** `EPIC-023A` (đọc cùng `_active_symbol`, không có phụ thuộc kỹ thuật bắt buộc — chỉ
  xếp sau vì rủi ro thấp hơn nên làm trước) · **Chặn:** `EPIC-023D`

## 1. Việc cần làm

Thay combo giả `_build_strategy_combo()` (`dev_board_panel.py:414-420`, hard-code
`["Manual", "SMA Crossover"]`, không nối gì) bằng card "Chiến lược" thật — Strategy/Interval
combo, %vốn/lệnh, đòn bẩy, nút "Thông số Chiến lược…", Nạp/Gỡ — dùng lại nguyên
`StrategyArmingCoordinator` + `build_bot_params_rows`/`build_bot_params_schema`/`parse_bot_params`.
Thêm card "Tín hiệu gần nhất" đọc `SignalFeed`.

## 2. Thay đổi theo file

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/screens/dashboard/dashboard_view_model.py` (`DashboardQmlViewModel`) | Thêm property/setter khớp `StrategyCardViewModel` Protocol: `selectedStrategyKey`, `liveInterval`, `sizingPercent`, `leverage`, `set_strategy_options()`, `set_strategy_selection()`, `set_bot_params()`, `set_bot_params_error()`, `lastSignalText`/`set_last_signal_text()`. |
| `src/presentation/ui/screens/dashboard/dev_board_panel.py` | Xoá `_build_strategy_combo()`/`_cbo_strategy` giả; thêm card Chiến lược thật + card Tín hiệu gần nhất (bố cục giống `trading_view.py::_build_strategy_card`/`_build_last_signal_card`), nối `armRequested`/`disarmRequested`/`strategyConfigChanged` vào ViewModel. |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | Dựng `self._strategy_arming = StrategyArmingCoordinator(...)` (instance riêng, `get_active_symbol=lambda: self._active_symbol`, `tracker` mới của riêng Dev Board — không dùng chung tracker với Trading, mỗi Presenter tự sở hữu theo `async-ui-action-rule.md` §2); gọi `restore_into_view_model()` sau khi ViewModel dựng xong; dựng `SignalFeed` riêng, nối `signalGenerated`. |
| `src/domain/strategies/base_strategy.py` và mọi implementer | Không đổi — `available_strategies` callback trỏ về registry hiện có, không phải khái niệm mới. |

## 3. Quyết định thiết kế

- `StrategyArmingCoordinator` đã nhận `dispatcher`/`view_model` qua `Protocol` — **không sửa file
  đó** (đúng §5 bảng "dùng chung, không sửa" ở README epic).
- Nạp ở Dev Board và nạp ở Trading là **cùng một hành động trên cùng một chiến lược đang chạy**
  (`ArmStrategyCommand` không tham số "màn nào gọi") — nạp ở màn này, màn kia mở lên sẽ thấy đúng
  chiến lược đó đã nạp (đọc qua `LiveStrategyConfigStore`/session, không phải trạng thái ViewModel
  cục bộ của từng màn).

## 4. Kiểm thử

Cùng khuôn `test_trading_presenter.py`'s phần strategy card + `test_strategy_arming_coordinator.py`
(coordinator không đổi, chỉ cần test construction/wiring phía Dev Board). Không sanity mới.
