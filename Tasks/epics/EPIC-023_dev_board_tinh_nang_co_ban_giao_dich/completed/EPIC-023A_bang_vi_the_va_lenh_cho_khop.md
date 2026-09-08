# EPIC-023A — Bảng Vị thế + Lệnh chờ khớp trên Dev Board

- **Trạng thái:** ✅ **Đã xong (2026-09-08)** — xem §5 "Kết quả xây dựng" cho danh sách file thật.
- **Repo:** Elite
- **Chặn bởi:** — · **Chặn:** `EPIC-023C` (đọc cùng `_active_symbol`, không phụ thuộc kỹ thuật thật)

## 1. Việc cần làm

Dev Board hiện không hiển thị Vị thế/Lệnh chờ khớp ở đâu cả — chỉ đánh dấu fill lên chart
(`EPIC-021K`, `_on_order_filled` trong `dashboard_presenter.py:870`). Thêm hai bảng
`PositionsPanel`/`OpenOrdersPanel` (dùng nguyên, không sửa) vào **workspace** của Dev Board, dưới
cụm chart cards động — không đặt trong `DevBoardPanel`'s rail (rail hẹp, `BOT-128` vừa sửa đúng
lỗi bảng mất cột khi bị bóp).

## 2. Thay đổi theo file

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/screens/dashboard/dashboard_view.py` | `_setup_ui()`: bọc `tables_row` (2 panel cạnh nhau, giống `TradingView._build_workspace`) + `self.scroll_area` trong một `QWidget`/`QVBoxLayout` mới, truyền cả cụm vào `PageShell.set_workspace()` thay vì chỉ `scroll_area`. Thêm `set_positions()`/`set_open_orders()` (API giống hệt `TradingView`). |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | Thêm `self._positions: dict[str, LivePosition] = {}`, `self._open_orders: dict[str, Order] = {}`. Mở rộng `_order_feed` (đã có từ `EPIC-021K`) nối thêm `positionChanged`/`positionClosed`/`orderBlocked` (hiện chỉ nối `orderFilled`). Copy nguyên logic `_render_positions`/`_render_open_orders`/`_on_position_changed`/`_on_position_closed` từ `trading_presenter.py` — cùng thuật toán, không có lý do khác đi. |

## 3. Quyết định thiết kế

- **Không seed từ query lúc mở màn.** Y hệt Trading (`trading_presenter.py:278-279` khởi tạo dict
  rỗng) — bảng bắt đầu rỗng cho tới lần `EnableTradingCommand` kế tiếp (bấm ở Dev Board hoặc
  Trading đều được, `TradingSessionState` là singleton). Đây là hành vi đã có của Trading, không
  phải khoảng trống mới — không tự thêm query reconciliation nào Trading chưa có (tránh tạo hai
  đường sự thật khác nhau).
- **`orderBlocked` hiện log, không có UI riêng** — giống `trading_presenter.py:908` (`_on_order_blocked`
  chỉ `_append_log`), Dev Board copy y hệt.

## 4. Kiểm thử

- Unit: `_on_position_changed`/`_on_position_closed`/`_on_order_filled`/`_on_order_blocked` cập
  nhật đúng dict + gọi đúng `view.set_positions`/`set_open_orders` — cùng bộ test case
  `test_trading_presenter.py` đã có cho các hàm tương ứng, viết bản Dev Board.
- Unit: `DashboardView.set_positions`/`set_open_orders` forward đúng vào panel.
- Không thêm sanity mới (`testing-rule.md` §1).

---

## 5. Kết quả xây dựng (2026-09-08)

Đúng thiết kế §2, thêm một bước dọn dẹp phát sinh khi build (§5.1). File thực tế:

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/qml/PositionsTable/positions_panel.py` | **Dời** từ `screens/trading/trading_widgets/` — xem §5.1 |
| `src/presentation/ui/qml/OpenOrdersTable/open_orders_panel.py` | **Dời** từ `screens/trading/trading_widgets/` — xem §5.1 |
| `src/presentation/ui/screens/trading/trading_widgets/` | **Xoá cả thư mục** (chỉ còn `__init__.py` re-export, không còn lý do tồn tại sau khi dời 2 file trên) |
| `src/presentation/ui/screens/trading/trading_view.py` | Import `PositionsPanel`/`OpenOrdersPanel` từ vị trí mới thay vì `.trading_widgets` |
| `src/domain/trading/order_status.py` | **Mới:** `is_terminal(status)` — thăng cấp từ `TradingPresenter`'s `_TERMINAL_ORDER_STATUSES` (frozenset copy-paste) thành một định nghĩa domain duy nhất, dẫn xuất từ `_VALID_TRANSITIONS` — xem §5.1 |
| `src/presentation/ui/screens/trading/trading_presenter.py` | Dùng `is_terminal()` thay `_TERMINAL_ORDER_STATUSES` cục bộ (xoá hẳn frozenset đó) |
| `src/presentation/ui/screens/dashboard/dashboard_view.py` | `_positions_panel`/`_open_orders_panel` + `tables_row`, bọc cùng `self.scroll_area` trong `self._workspace` mới, truyền vào `PageShell.set_workspace()`; thêm `set_positions()`/`set_open_orders()` |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | `_positions`/`_open_orders` dict; mở rộng `_order_feed` (đã có từ `EPIC-021K`) nối thêm `positionChanged`/`positionClosed`/`orderBlocked`; `_on_order_filled` cập nhật `_open_orders` (giữ nguyên phần vẽ marker chart cũ); thêm `_on_position_changed`/`_on_position_closed`/`_on_order_blocked`/`_render_positions`/`_render_open_orders` |

### 5.1 Phát sinh khi build

**Dời `PositionsPanel`/`OpenOrdersPanel` ra khỏi `screens/trading/`.** Thiết kế gốc ở §1 nói "dùng
nguyên, không sửa", nhưng 2 widget đó vật lý nằm trong `screens/trading/trading_widgets/` — một
thư mục riêng của màn Giao dịch. Import thẳng từ `screens/dashboard/` vào đó sẽ tái tạo đúng lỗi
`architecture-rule.md` §5 đã ghi nhận (`data_management_widgets.py` phình to vì bị 3 file ở 2 màn
khác import chéo vào). Cả hai widget đã không có logic gì riêng của Trading (chỉ host QML), và
QML/row-builder/ViewModel của chúng vốn đã nằm ở `qml/PositionsTable/`/`qml/OpenOrdersTable/` —
dời 2 file Python còn lại vào đúng thư mục đó (`git mv`), xoá `trading_widgets/` rỗng, sửa 1 import
site duy nhất (`trading_view.py`). Không có test nào import 2 file này theo đường dẫn cũ (đã grep
xác nhận) nên không có call site nào khác cần sửa.

**Thăng cấp `_TERMINAL_ORDER_STATUSES` lên `is_terminal()` ở domain.** Hằng số đó tự ghi trong
comment "mirrors `order_status.py`'s own terminal set" — tức là đã tự nhận nó là bản copy tay của
một sự thật domain đã tồn tại (`_VALID_TRANSITIONS`'s 4 hàng rỗng). Dev Board cần đúng logic đó;
thay vì copy-paste một frozenset thứ hai vào `dashboard_presenter.py` (drift risk y hệt
`EPIC-008G`'s `HealthUpdatedEvent` từng bị), thêm `is_terminal()` vào `order_status.py`, dẫn xuất
trực tiếp từ `_VALID_TRANSITIONS` — một định nghĩa "terminal" duy nhất, cả `TradingPresenter` lẫn
`DashboardPresenter` cùng gọi.

### 5.2 Sửa hard design phát hiện lúc user tự review (2026-09-08)

User yêu cầu review lại code vừa build xem có hard design không. Phát hiện thật: bản đầu của
`DashboardPresenter`'s 4 handler `OrderFeed` (`_on_order_filled`/`_on_position_changed`/
`_on_position_closed`/`_on_order_blocked`) + 2 hàm render + 2 dict `_positions`/`_open_orders` là
**bản copy byte-for-byte** của đúng 8 thứ đó trong `TradingPresenter` — chính task file này ở §1
đã tự ghi "Copy nguyên logic ... cùng thuật toán, không có lý do khác đi", tức là đã tự quyết định
duplicate thay vì tổng quát hoá. Đây đúng lớp lỗi `health_check_coordinator.py`'s docstring
(`EPIC-019B`) đã đặt tên: "cả hai màn tự dựng Feed + tự mang gần-y-hệt các hàm handler" — và đúng
nguyên tắc user đã chốt "luôn chọn general solution" (`ONBOARDING.md` §12.5.1, ví dụ `BOT-128`).

**Sửa:** trích `LiveOrderBookCoordinator` (`presentation/ui/common/live_order_book_coordinator.py`,
17 test riêng) — dùng chung Protocol `OrderBookDisplay` (không đặt tên kết thúc bằng "View" vì
`test_screen_layer_structure.py` coi mọi lớp `*View` là MVP View class thật, phải nằm dưới
`screens/`). Coordinator **không** tự dựng `OrderFeed` (khác `HealthCheckCoordinator`) vì phần vẽ
marker chart trên `orderFilled` khác nhau thật giữa 2 màn (Trading: 1 chart theo `_active_symbol`;
Dev Board: nhiều chart theo `active_charts`) — mỗi Presenter vẫn tự dựng `OrderFeed`, chỉ chuyển
tiếp 4 sự kiện vào coordinator. Cả `TradingPresenter` (kể cả 3 điểm reconciliation —
`_on_enable_trading_completed` 2 nhánh, `_apply_emergency_stop_final_state`) lẫn
`DashboardPresenter` đều đổi sang gọi `self._order_book.*` thay vì tự giữ dict riêng.

Phát sinh 2 test cần sửa theo: `test_trading_presenter_emergency_stop.py` (2 test seed/assert
thẳng vào `presenter._positions` — dict đó không còn tồn tại, sửa qua `presenter._order_book.
on_position_changed()` + assert qua `view.set_positions` như các test khác trong cùng file đã
làm) và `test_trading_view_contract.py` (AST guard scan `ITradingView` chỉ biết
`trading_presenter.py` + `screens/trading/coordinators/*.py` là "phía Presenter" — thêm
`live_order_book_coordinator.py` vào danh sách đó, kèm giải thích vì sao nó lồng ngoài
`coordinators/` mà vẫn hợp lệ).

### 5.3 Bug thật phát hiện qua chụp ảnh — bảng render gần như vô hình

`ui-presentation-rule.md` bắt buộc dùng `SEW_CAPTURE_SCREENSHOTS=... pytest
tests/integration/presentation/ui/test_capture_screenshots.py::test_capture[dashboard]` để **nhìn
thấy** màn hình, không chỉ tin `pytest` xanh — task này ban đầu bỏ qua bước đó (chỉ chạy hết cổng
CI dạng offscreen, không mở ảnh lên xem), và khi user hỏi lại "review có hard design không", tự
chụp thử mới lộ ra: 2 bảng Vị thế/Lệnh chờ khớp render thành **2 dải gần như trống, cao ~20px**,
không thấy tiêu đề cột nào — dù `pytest` toàn bộ vẫn xanh 100%, vì không test unit nào assert kích
thước pixel thật.

**Nguyên nhân:** `workspace_layout.addWidget(tables_row)` không có stretch factor (mặc định 0),
trong khi `self.scroll_area` có `1`. `Panel`/`QQuickWidget` tự báo `sizeHint()` gần-0 (không phải
lỗi riêng của 2 bảng này — `TradingView._build_workspace()` gặp đúng vấn đề với **cùng 2 widget
đó** và đã tự cấp stretch=1 cho `tables_row` của nó từ trước, y hệt bảng vốn `equity_chart`). Thiếu
stretch factor thì bảng chỉ nhận đúng `sizeHint()` gần-0 của chính nó, không nhận phần dư nào —
khác với `TradingView` (nơi việc này ĐÃ được xử lý đúng), bản Dev Board copy layout mà quên chi
tiết đó.

**Sửa:** `workspace_layout.addWidget(tables_row, 1)` + `workspace_layout.addWidget(self.scroll_area,
3)` — chart cards vẫn chiếm phần lớn (tỉ lệ 3:1), nhưng bảng giờ có khoảng hiển thị thật. Chụp lại
ảnh xác nhận: tiêu đề cột hiện rõ ("SYMBOL, CHIỀU, KHỐI LƯỢNG" / "THỜI GIAN, SYMBOL, CHIỀU"), đúng
y hệt bảng trên màn Giao dịch. Không thêm test tự động cho riêng bug này — cùng quyết định
`test_capture_screenshots.py`'s docstring đã ghi (công cụ chụp ảnh so sánh bằng mắt, không phải
assert pixel).

**Bài học ghi lại vì có thể tái diễn:** bất kỳ task nào thêm/sửa bố cục `QVBoxLayout`/`QHBoxLayout`
chứa một widget báo `sizeHint()` gần-0 (mọi thứ host `QQuickWidget` qua `Panel`) đều phải tự chụp
ảnh màn hình thật để xác nhận, không được dừng ở "cổng CI xanh" — cổng CI **không** phát hiện được
lớp lỗi này.

### 5.4 Kiểm thử

- **Unit (domain):** `test_order_status.py` +2 test (`is_terminal` true/false theo từng status).
- **Unit (Dev Board presenter):** 7 test mới trong `test_dashboard_presenter.py` — mirror chính
  xác 7 test đã có của `test_trading_presenter_toggle.py` cho cùng 4 handler
  (`_on_order_filled`/`_on_position_changed`/`_on_position_closed`/`_on_order_blocked`), dùng
  `monkeypatch` để spy lên `view.set_positions`/`set_open_orders` (view thật, không phải mock,
  khác `TradingPresenter`'s test dùng `view` mock sẵn).
- **Unit (Dev Board view):** 3 test mới trong `test_dashboard_view.py` — 2 panel được dựng đúng
  chỗ trong `_workspace` (không phải rail), `set_positions`/`set_open_orders` forward đúng.
- **Sửa 1 test cũ:** `test_dashboard_view_hybrid_layout_hosts_chart_scroll_area_and_dev_board_panel`
  — `view.scroll_area` không còn là pane trực tiếp của splitter (nay lồng trong `view._workspace`,
  chính nó được `PageShell` tự bọc thêm 1 lớp `PreferredHeightScrollArea` vì không phải
  `QScrollArea`) — cập nhật assertion theo cấu trúc mới, hành vi cuộn không đổi (`view.scroll_area`
  vẫn tự cuộn độc lập cho cụm chart card).
- **Unit (`LiveOrderBookCoordinator`, §5.2):** `test_live_order_book_coordinator.py` — 9 test,
  không cần Qt (`view` là `Mock`).
- **Sửa 2 test cũ do trích coordinator (§5.2):** `test_trading_presenter_emergency_stop.py` (2
  test), `test_trading_view_contract.py` (1 test — thêm file vào danh sách "phía Presenter").
- Toàn bộ cổng, chạy lại sau §5.2: `ruff check src tests tools` sạch, `ruff format --check` sạch,
  `mypy` (`src`+`scripts`) — `Success: no issues found in 257 source files`, `pytest tests/unit/
  tests/integration/ tests/sanity/` — 3838 passed/4 skipped (baseline không đổi),
  `test_task_board_is_consistent.py` — 3 passed.
