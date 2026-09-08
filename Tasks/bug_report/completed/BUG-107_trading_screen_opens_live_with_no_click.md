# BUG-107 — Opening the Trading screen (a real user click) still auto-starts a live Binance stream

**Reported date:** 2026-09-08
**Fixed date:** 2026-09-08
**Severity:** 🟡 P2 — no money at risk (order placement stays gated behind the separate "Bật giao
dịch" toggle, off by default), but the app performs real, unrequested network activity from a
click that only meant "show me this screen".
**Status:** ✅ Fixed — see §3.

---

## 1. Hiện tượng (Symptom)

User gửi log thật khi mở màn Giao dịch:

```text
09:45:51,631 - App - INFO - UI Layer Ready — MainWindow rendered and Qt event loop active.
09:46:08,258 - App.ChartCard - INFO - [chart-env] ChartCard(ETHUSDT): ...
09:46:08,409 - App - INFO - Executing command: SyncMarketDataCommand
09:46:09,075 - App.ExchangeClient - INFO - Streaming historical klines for ETHUSDT at 1m ...
09:46:13,350 - App.ExchangeClient - INFO - Successfully streamed 7009 klines for ETHUSDT.
09:46:13,363 - App - INFO - Executing command: StartLiveStreamCommand
09:46:16,183 - App.LiveStream - INFO - [Live Stream] ETHUSDT | Price: 2490.89 | ...
```

Không có dòng nào ở giữa ghi lại một cú bấm "Enable Trading" hay tương đương — 17 giây sau khi UI
sẵn sàng, app đã tự sync + mở websocket. User hỏi thẳng: *"i have spec app will not save UI state,
what this behaviour still remaining?"*

## 2. Không phải `BUG-104` tái phát — là phần `BUG-104` cố tình để lại

`BUG-104` (đóng 2026-09-03) sửa đúng vế "mở **app** lên, chưa bấm gì, mà vẫn nhảy vào Trading và
chạy live" — bằng cách bỏ hẳn việc nhớ `last_route`. Hồ sơ đó ghi rõ quyết định:

> `TradingPresenter` giữ nguyên thiết kế, chỉ chạy khi user tự tay bấm vào Trading.

Đúng — nhưng "tự tay bấm vào Trading" **chính nó** vẫn kích hoạt live, vì thiết kế gốc của
`EPIC-021I` (comment cũ trong `chart_coordinator.py`, trước bug này): *"the chart is always live
while this screen is open"*. `TradingPresenter.__init__` gọi thẳng `ChartCoordinator.start()`, và
`_run()` khi đó không có nhánh nào khác ngoài "sync rồi mở stream". Log của user khớp chính xác:
route-restore đã bị `BUG-104` bịt, nhưng cú **click sidebar thật** vào Trading vẫn đủ để tự động
sync + live — đúng cái comment gốc `EPIC-021I` mô tả, chưa bao giờ được coi là bug cho tới hôm nay.

## 3. Fix

**`ChartCoordinator.start()`** (`src/presentation/ui/screens/trading/coordinators/chart_coordinator.py`)
thêm tham số `go_live: bool = False`. `_run()` chỉ dispatch `SyncMarketDataCommand` +
`StartLiveStreamCommand` khi `go_live=True`; nếu không, chỉ đọc lịch sử **local** qua
`GetHistoricalKlinesQuery` — không network.

**`TradingPresenter`** đọc config key mới `TRADING_CHART_AUTOSTART_ENABLED` (mặc định `False`) —
đúng khuôn Dev Board đã có sẵn cho chính vấn đề này (`DEV_BOARD_AUTOSTART_ENABLED`, `BOT-062`).
Mở màn hình luôn gọi `start(..., go_live=self._chart_live_requested)` với giá trị đọc từ config
đó — mặc định tắt, nên mặc định chỉ đọc local history.

**Hành động thật sự bật live: `EnableTradingCommand` thành công.** `_go_live_if_not_already()`
được gọi trong `_on_enable_trading_completed()` khi `result.enabled` — đây mới là chỗ user thật sự
"yêu cầu giá live", vì bật giao dịch mà không có giá live là giao dịch mù. Một khi đã live, tắt
giao dịch lại **không** dừng stream (stream dùng chung toàn tiến trình, Dev Board có thể đang phụ
thuộc vào nó — cùng ràng buộc `shutdown()` đã ghi từ trước).

**Một lỗi tự gây ra, bắt được trước khi commit:** bản nháp đầu cho `_go_live_if_not_already()` đi
qua `_restart_chart()` — hàm này luôn gọi `stop()` trước `start()`. Với promotion-lên-live **lần
đầu**, `stop()` chạy trong khi màn hình **chưa từng** tự mở stream nào — dispatch
`StopLiveStreamCommand` không cần thiết, và vì lệnh đó không mang định danh người gọi
(`stop_stream()` không nhận tham số), nó có thể giết luôn stream Dev Board đang chạy. Phát hiện
bằng chính test đầu tiên viết cho path này (`mock_dispatcher.dispatch.assert_called_once_with(...)`
đỏ vì bị gọi 2 lần) — sửa: promotion lần đầu không gọi `stop()`; `_restart_chart()` (đổi
symbol/timeframe) chỉ gọi `stop()` khi màn hình **đang** tự sở hữu stream
(`self._chart_live_requested`).

**Thêm 1 dòng log minh bạch** khi chỉ đọc local: *"Đang tải dữ liệu … từ cơ sở dữ liệu cục bộ
(chưa kết nối trực tiếp — bật giao dịch để kết nối)"* — để trạng thái "chưa live" nhìn thấy được
trên panel log, không chỉ suy luận từ việc thiếu dòng "Đang mở luồng trực tiếp".

## 4. Test

12 test mới:

| File | Ghim cái gì |
| :--- | :--- |
| `coordinators/test_chart_coordinator.py` (4 test) | `go_live=False` không dispatch Sync/Start; `go_live=True` có cả hai; `stop()` luôn dispatch (vô điều kiện — caller tự quyết định có gọi hay không); `start()` mặc định `go_live=False` |
| `test_trading_presenter_chart_autostart.py` (8 test) | Construction chỉ submit local history; construction không chạm dispatcher; opt-in config đi live ngay lúc mở; bật giao dịch thành công mới đi live; bật giao dịch thất bại không đi live; promotion lần đầu **không** gọi `stop()`; đổi symbol trước khi live **không** gọi `stop()`; đổi symbol sau khi đã live **có** gọi `stop()` rồi live lại đúng symbol mới |

Cả 2 quyết định dễ sai nhất (mặc định tắt; không `stop()` một stream mình chưa từng mở) đã
mutation-verify thật: đảo `_DEFAULT_CHART_AUTOSTART_ENABLED` → đỏ; bỏ điều kiện guard `stop()` →
đỏ.

`mock_config`/`container`/`view`/`presenter` — cùng 4 fixture đã byte-identical ở
`test_trading_presenter_toggle.py` và `..._emergency_stop.py` từ trước — dời vào
`tests/unit/presentation/ui/screens/trading/conftest.py` chung, không sửa 2 file gốc (fixture cục
bộ trong module vẫn thắng fixture cùng tên ở `conftest.py`, nên hành vi 2 file đó không đổi).

## 5. Chưa làm — đã tách task riêng, có lý do

`chart_coordinator.py`'s docstring gốc từ `EPIC-021I` đã tự ghi nhận một giới hạn kiến trúc thật:
`ILiveStreamService` là **một** stream dùng chung toàn tiến trình, không theo từng màn hình —
"ai gọi `StartLiveStreamCommand` sau cùng quyết định ai nhận tick", và `stop()` không nhận tham số
định danh nên dừng của một màn có thể giết stream màn khác. Bug này phải thêm một guard
(`self._chart_live_requested`) đúng để né đúng cái giới hạn đó, không phải sửa nó.

**Cố tình không gộp việc thiết kế lại quyền sở hữu stream (refcount theo màn/symbol) vào bug fix
này** — nó đổi một interface dùng chung giữa 2 màn hình, lớn hơn hẳn phạm vi "mở màn không được tự
ra mạng". Đã mở thành task riêng (`spawn_task`, chưa có mã task board).
