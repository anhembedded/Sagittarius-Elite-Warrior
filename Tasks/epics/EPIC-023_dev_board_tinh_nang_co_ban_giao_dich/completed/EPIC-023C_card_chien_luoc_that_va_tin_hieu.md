# EPIC-023C — Card "Chiến lược" thật (Nạp/Gỡ) + Tín hiệu gần nhất

- **Trạng thái:** ✅ **Đã xong (2026-09-08)** — xem §5 "Kết quả xây dựng".
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

---

## 5. Kết quả xây dựng (2026-09-08)

Đúng thiết kế §2/§3, cộng promotion `StrategyArmingCoordinator`/`StrategyParamsDialog` ra khỏi
`screens/trading/` (§5.1 — cùng lý do `EPIC-023A`/`B` đã dời `PositionsPanel`/`equity_chart_adapter.py`),
và **một bug thật đã có từ trước, không phải do epic này gây ra** mà lần đầu tiên bị một test thật
bắt được (§5.2).

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/common/strategy_arming_coordinator.py` | **Dời** từ `screens/trading/coordinators/`, đổi tên Protocol `BotParamsView` → `BotParamsSink` (tránh guard `test_screen_layer_structure.py`). Sửa bug thật (§5.2). |
| `src/presentation/ui/components/strategy_params/strategy_params_dialog.py` | **Dời+đổi tên** từ `screens/trading/trading_strategy_params_dialog.py`, `TradingStrategyParamsDialog` → `StrategyParamsDialog`. |
| `src/presentation/ui/screens/dashboard/dashboard_view_model.py` | Thêm nguyên khối Property/Signal/Slot card Chiến lược + Tín hiệu gần nhất — **chép lại từ `TradingViewModel`**, không kế thừa base class chung (giới hạn Shiboken: một `QObject` không thể kế thừa `Property`/`Signal` từ 2 base độc lập — xem `architecture-rule.md` §2.1). |
| `src/presentation/ui/screens/dashboard/dev_board_panel.py` | Xoá `_build_strategy_combo()`/`_cbo_strategy` giả; thêm `_build_strategy_card()`/`_build_last_signal_card()`. 3 hàm sync đổi tên `_apply_*` → `_sync_strategy_options/_sync_strategy_selection/_sync_armed_summary` cho khớp quy ước đặt tên đã có sẵn 100% trong file này (§5.3). |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | Dựng `self._strategy_session`/`self._arm_tracker`/`self._arming_coordinator` riêng của Dev Board (không dùng chung tracker với Trading — đúng `async-ui-action-rule.md` §2); dựng `SignalFeed` riêng, nối `signalGenerated` → `_on_signal_generated`. |
| `tests/integration/presentation/ui/conftest.py` | `mock_dispatch` chạy thật `ArmStrategyCommandHandler`/`DisarmStrategyCommandHandler` (thay vì rơi vào nhánh `_FakeResponse` chung) — cần cho §5.2's test thật sự đi qua `LiveStrategySession`. |

### 5.1 Phát sinh khi build: dời `StrategyArmingCoordinator`/`StrategyParamsDialog` ra `common/`/`components/`

Y hệt lý do `EPIC-023A`/`B` đã dời `PositionsPanel`/`equity_chart_adapter.py`: cả hai đã nhận mọi
phụ thuộc qua `Protocol`/tham số tường minh (`CommandDispatcher`, `StrategyCardViewModel`,
`BotParamsSink`), không tham chiếu trực tiếp `TradingPresenter`/`TradingViewModel` — dời là đổi
đường dẫn thuần, không đổi logic bên trong.

### 5.2 Bug thật tìm được: `StrategyArmingCoordinator.arm()`/`disarm()` gọi sai chữ ký `dispatch()`

`arm()`/`disarm()` gọi `self._dispatcher.dispatch(ArmStrategyCommand(...))` — **một** đối số. Chữ ký
thật của `IDispatcher.dispatch()` (engine) là `dispatch(handler_class, input_dto)` — **hai** đối số,
đúng như mọi call site khác trong repo (`stream_lifecycle_controller.py`, mọi `coordinators/*.py`
khác). Gọi thiếu đối số này **có từ trước `EPIC-023C`** — nguyên trong `TradingPresenter` gốc, chỉ
được dời sang `common/` nguyên vẹn ở §5.1 — nhưng chưa từng bị phát hiện vì:

1. Mọi unit test dùng `dispatcher` là `MagicMock`, chấp nhận bất kỳ số đối số.
2. Chưa từng có test click nút Nạp/Gỡ thật, xuyên qua `IDispatcher` thật, cho **cả 2 màn**.

Test mới của epic này (`test_strategy_dropdown_arms_the_selected_strategy`,
`tests/integration/presentation/ui/test_dev_board_known_gaps.py`) là test đầu tiên trong toàn repo
làm điều đó, và bắt được ngay ở lần chạy full suite đầu tiên
(`AttributeError: 'ActionOwnershipTracker' object has no attribute 'start_action'` — một bug thứ
hai, cũng có từ trước: gọi `self._tracker.start_action(...)` — phương thức thật là `begin_action()`,
nhận 3 đối số `(kind, config, previous_state)`, không bao giờ trả `None`).

**Sửa:** `strategy_arming_coordinator.py` — `begin_action(kind, None, None)` (bỏ nhánh `if action is
None` vô nghĩa), `dispatch(ArmStrategyCommandHandler, ArmStrategyCommand(...))`/
`dispatch(DisarmStrategyCommandHandler, DisarmStrategyCommand())`; `CommandDispatcher` Protocol sửa
chữ ký khớp `IDispatcher` thật. `tests/unit/presentation/ui/common/test_strategy_arming_coordinator.py`
2 assertion đọc `call_args.args[0]` (cứ tưởng là command) sửa thành `args[1]` (đối số thứ hai mới
đúng là command; `args[0]` là handler class). `tests/integration/presentation/ui/conftest.py`'s
`mock_dispatch` thêm nhánh gọi thật `ArmStrategyCommandHandler`/`DisarmStrategyCommandHandler` với
`LiveStrategySession`/`TradingSessionState` lấy từ container — bắt buộc, vì `armed_summary()` đọc
trạng thái từ `LiveStrategySession.config`, thứ chỉ handler thật mới cập nhật (một `_FakeResponse`
giả không chạm tới).

**Chưa sửa, đã tách task riêng** (`task_b32d74cd`, spawned trong session này): trên một máy hoàn
toàn mới (chưa từng lưu `trading.live_interval`), combo Khung TG tự hiện "1m" (Qt tự chọn item đầu
khi `addItems()`) nhưng `viewModel.liveInterval` vẫn `""` — người dùng bấm Nạp lần đầu sẽ bị chặn
âm thầm bởi `MISSING_SYMBOL_OR_INTERVAL` dù giao diện nhìn như đã chọn sẵn. Lỗi này có ở **cả hai
màn** (dùng chung `StrategyArmingCoordinator.restore_into_view_model()`), không phải riêng Dev
Board, và là quyết định thiết kế (nên tự chọn interval đầu tiên khi chưa có gì lưu?) chứ không phải
one-line fix — để task riêng quyết định.

### 5.3 Phát sinh khi build: đổi tên 3 hàm sync trong `dev_board_panel.py` cho nhất quán

`_apply_strategy_options`/`_apply_strategy_selection`/`_apply_armed_summary` chép nguyên quy ước đặt
tên `_apply_*` từ `trading_view.py`, nhưng 7 hàm sync khác đã có sẵn trong `dev_board_panel.py`
(`_sync_start_date`, `_sync_end_date`, `_sync_symbol`, `_sync_price_ticker`, `_sync_ws_status`,
`_sync_controls_active`, `_sync_progress`) đều dùng `_sync_*` nhất quán 100%. Đổi lại thành
`_sync_strategy_options`/`_sync_strategy_selection`/`_sync_armed_summary` cho khớp quy ước riêng của
file này, không lẫn quy ước của file khác.

### 5.4 Kiểm thử

- **Unit:** `test_strategy_arming_coordinator.py` (dời từ `test_trading_strategy_arming.py`, sửa
  2 assertion §5.2) — thêm fixture `strategy_registry` cục bộ (không cross-import fixture từ
  `screens/trading/conftest.py`, đúng quy ước "restate, không cross-import" của file này).
  `test_dashboard_presenter.py` — ~11 test mới (construction card Chiến lược, arm/disarm delegation,
  lọc tín hiệu theo symbol, armed-config-changed) + fixture `strategy_registry`/`strategy_session`
  thật (không phải `MagicMock`, vì `armed_summary()` f-string-format các field của nó).
- **Integration:** `test_dev_board_known_gaps.py::test_strategy_dropdown_arms_the_selected_strategy`
  — viết lại từ test cũ khẳng định combo giả "không có tác dụng gì" (đúng lời dặn trong docstring
  test cũ: phải viết lại, không xoá, khi control được nối thật). Đây là test bắt được cả 2 bug ở
  §5.2. `test_dashboard_integration.py`/`test_dashboard_live_stream.py` — fixture `mock_app` cần
  `StrategyRegistry`/`LiveStrategySession` thật trong `resolve_side_effect`.
- **Xác minh bằng mắt:** `SEW_CAPTURE_SCREENSHOTS=... test_capture_screenshots.py::test_capture[dashboard]`
  — card "Chiến lược" + "Tín hiệu gần nhất" hiện đúng layout, không lặp lại lỗi squeeze `EPIC-023A`
  §5.3.
- Toàn bộ cổng: `ruff check`/`ruff format --check` sạch, `mypy --config-file pyproject.toml
  --namespace-packages --explicit-package-bases src scripts` — `Success: no issues found in 257
  source files`, `pytest tests/unit/ tests/integration/ tests/sanity/` — **3848 passed, 4 skipped**
  (toàn bộ, không riêng phần Dev Board).
