# EPIC-023 — Dev Board có các tính năng cơ bản của màn Giao dịch

- **Trạng thái:** ✅ Hoàn thành (4/4 task con)
- **Repo:** Elite
- **Lập ngày:** 2026-09-08, theo yêu cầu trực tiếp của user: "dev board cần có các tính năng cơ
  bản của màn hình giao dịch, để cho test các tính năng cơ bản đó"
- **Quyết định đã chốt với user (2026-09-08):** Dev Board có **toàn quyền** điều khiển giao dịch
  thật — Nạp/Gỡ chiến lược, Bật/Tắt giao dịch, Dừng khẩn cấp — giống hệt màn Giao dịch, không chỉ
  hiển thị. Lý do user chọn: dev cần test được **trọn vòng đời** một chiến lược (nạp → sinh tín
  hiệu → khớp lệnh → vị thế) ngay tại Dev Board, không phải chuyển màn.

---

## 1. Vấn đề thật

Dev Board (`DashboardPresenter`/`DevBoardPanel`) tự nhận mình là "developer testbed... kiểm thử
chỉ báo & script trên dữ liệu trực tiếp" — nhưng cái nó thật sự kiểm thử được chỉ là **chỉ báo**
(indicator scripts vẽ đường/tô nền lên chart), không phải **chiến lược sống** (live strategy sinh
tín hiệu, đặt lệnh, mở vị thế). Combo "Strategy: Manual/SMA Crossover" trên Dev Board đã tồn tại
từ trước — nhưng là **hàng giả**: `_build_strategy_combo()` chỉ `addItems(["Manual", "SMA
Crossover"])`, không có handler, không dispatch `ArmStrategyCommand`, không đọc `LiveStrategyConfig`
nào cả (đo bằng `grep`, không phải suy đoán — xem `dev_board_panel.py:414-420`).

Kết quả: muốn xem một chiến lược **thật sự** cư xử thế nào trên dữ liệu live — có sinh tín hiệu
đúng lúc không, lệnh có khớp không, vị thế/vốn biến động ra sao — bắt buộc phải mở màn Giao dịch,
dù đang chỉ muốn *quan sát*, không phải giao dịch thật với tài khoản chính.

## 2. Cái đã có và tái dùng được — đừng viết lại

Toàn bộ hạ tầng dưới đây đã tồn tại, được `EPIC-021`/`EPIC-022` xây cho màn Giao dịch, và **đã
viết theo Protocol/Feed dùng chung** — không cột cứng vào `TradingPresenter`/`TradingViewModel`:

| Cần gì | Đã có sẵn, dùng lại nguyên vẹn |
| :--- | :--- |
| Nạp/Gỡ chiến lược + form Thông số | `StrategyArmingCoordinator` (`coordinators/strategy_arming_coordinator.py`) — nhận `view_model`/`dispatcher` qua `Protocol`, không import `TradingViewModel` |
| Bảng Vị thế / Lệnh chờ khớp | `PositionsPanel`/`OpenOrdersPanel` (widget QML tự chứa, `set_rows()`), `build_position_row`/`build_open_order_row` (hàm thuần ở `qml/*/*.py`, không riêng của Trading) |
| Trạng thái Vị thế/Lệnh chờ cập nhật live | `OrderFeed` (`orderFilled`/`positionChanged`/`positionClosed`/`orderBlocked`) — **Dev Board đã tự dựng instance riêng từ `EPIC-021K`** (đánh dấu fill lên chart), chỉ cần thêm handler đọc đủ 4 sự kiện thay vì 1 |
| Đường vốn (equity) | `EquityFeed` + `EquityCurveRecorder` (DI singleton, seed backlog) — `EquityChartAdapter` viết riêng cho Trading (`EPIC-021M` §2.4 phương án 2, tránh phụ thuộc ngược `backtest/`) — Dev Board tái dùng cùng adapter |
| Tín hiệu gần nhất | `SignalFeed` (`signalGenerated`) — cùng khuôn Feed |
| Bật/Tắt giao dịch, Dừng khẩn cấp | `EnableTradingCommand`/`DisableTradingCommand`/`EmergencyStopCommand` — account-wide, đọc/ghi `TradingSessionState` (DI singleton) |
| Thống kê phiên | `TradingSessionState.orders_sent_this_session`/`known_open_symbols` — cùng singleton mọi màn đọc |

**Vì sao không đụng gì tới `Trading`:** mọi thứ ở bảng trên đều là **trạng thái toàn hệ thống**
(account-wide), không phải sở hữu riêng của màn Giao dịch — giống hệt lý do `BOT-126` làm
`ILiveStreamService` đếm tham chiếu theo owner thay vì "ai gọi sau cùng thắng": hai màn cùng đọc/ghi
một sự thật không phải là xung đột, miễn mỗi màn tự dựng **instance Feed riêng** của mình (đúng
khuôn `OrderFeed`/`MarketTickFeed` Dev Board đã làm từ `EPIC-021K`/trước đó — guard test
`test_one_event_is_not_subscribed_by_two_presenters` chỉ cấm `event_bus.on()` **trực tiếp** trong
`screens/`, không cấm hai màn cùng dùng một Feed **class**, đó chính xác là lý do Feed tồn tại).

**Rủi ro đã cân nhắc:** hai màn cùng có nút Bật/Tắt giao dịch/Nạp chiến lược thật — nhưng vì cả hai
đọc/ghi CÙNG MỘT `TradingSessionState`/`LiveStrategyConfigStore` singleton, bấm ở màn nào cũng ra
kết quả giống hệt (không có "trạng thái Dev Board" và "trạng thái Trading" tách biệt) — đúng tinh
thần user chốt ở §0.

## 3. Mục tiêu

Kết thúc epic, một dev đứng ở Dev Board phải làm được đúng chuỗi này **mà không cần rời màn**:

1. Chọn Symbol/Interval, Load History (đã có sẵn).
2. Chọn chiến lược thật ở card "Chiến lược", Nạp — thấy tóm tắt đã nạp.
3. Bật giao dịch — thấy Vị thế/Lệnh chờ khớp/Vốn/Tín hiệu gần nhất cập nhật sống khi chiến lược
   tự sinh lệnh trên dữ liệu live.
4. Dừng khẩn cấp — mọi lệnh chờ bị huỷ, vị thế đóng, giao dịch tắt, y hệt màn Giao dịch.

**Ngoài phạm vi, cố ý:** không tạo "phiên Dev Board" tách biệt "phiên Trading" — cả hai luôn cùng
một trạng thái thật (§2). Không đổi bất kỳ file nào dưới `screens/trading/` trừ khi phát sinh bug
thật khi build (theo đúng tinh thần `EPIC-021M`'s §6.1 "phát sinh khi build").

## 4. Thứ tự thực hiện — xếp theo rủi ro tăng dần

Nhóm A/B chỉ **đọc** (dựng Feed, hiển thị) — rủi ro thấp nhất, làm trước. Nhóm C **ghi** nhưng bị
chặn khi đang bật giao dịch (`EPIC-022` §4.1). Nhóm D là hành động ảnh hưởng thật nhất (bật giao
dịch thật/testnet, dừng khẩn cấp) — làm sau cùng, soát kỹ nhất.

| # | Task | Chặn bởi | Trạng thái |
| :-: | :--- | :--- | :---: |
| **A** | [Bảng Vị thế + Lệnh chờ khớp trên Dev Board](completed/EPIC-023A_bang_vi_the_va_lenh_cho_khop.md) | — | ✅ |
| **B** | [Biểu đồ Vốn (equity) trên Dev Board](completed/EPIC-023B_bieu_do_von_realtime.md) | — | ✅ |
| **C** | [Card "Chiến lược" thật — Nạp/Gỡ + Tín hiệu gần nhất](completed/EPIC-023C_card_chien_luoc_that_va_tin_hieu.md) | A (đọc cùng `_active_symbol`) | ✅ |
| **D** | [Bật/Tắt giao dịch + Dừng khẩn cấp + Thống kê phiên](completed/EPIC-023D_bat_tat_giao_dich_va_dung_khan_cap.md) | A, C | ✅ |

---

## 5. Bố cục — cái gì dùng chung, cái gì riêng từng màn

`ui-presentation-rule.md`/`12.5.2` — không dựng lại widget, chỉ lắp thêm dây nối riêng của Dev Board:

| Lớp | Dùng chung (không sửa) | Riêng Dev Board (mới) |
| :--- | :--- | :--- |
| Widget | `PositionsPanel`, `OpenOrdersPanel`, `ChartCard` (equity), `strategy_params` form builders | Cách sắp bố cục trong `DevBoardPanel`/`DashboardView` (rail hẹp không đủ chỗ cho bảng nhiều cột — xem `BOT-128`; tables/equity đặt ở **workspace**, không phải rail) |
| Coordinator | `StrategyArmingCoordinator` (Protocol, không sửa) | `DashboardPresenter` tự dựng instance riêng, tự cấp `ActionOwnershipTracker`, `get_active_symbol=lambda: self._active_symbol` |
| Feed | `OrderFeed`, `EquityFeed`, `SignalFeed` (class dùng chung, `common/`) | `DashboardPresenter` tự dựng instance riêng của mỗi Feed (đúng khuôn đã có với `MarketTickFeed`/`OrderFeed` từ trước) |
| Command | `ArmStrategyCommand`/`DisarmStrategyCommand`/`EnableTradingCommand`/`DisableTradingCommand`/`EmergencyStopCommand` (không sửa) | — (dispatch y hệt, không tham số nào riêng cho "màn nào gọi") |
| ViewModel | — | `DashboardQmlViewModel` cần thêm property mới (strategy card, toggle, session stats) — xem từng task con |

Không cần PlantUML as-is/to-be: không file nào của `screens/trading/` bị sửa cấu trúc (chỉ thêm
dây nối phía Dev Board đọc/ghi cùng trạng thái có sẵn), nên đây là bổ sung tính năng, không phải
tái cấu trúc theo nghĩa `12.5.3`.
