# EPIC-022E — Vẽ chiến lược lên chart live + card TÍN HIỆU GẦN NHẤT

**Status:** ✅ Hoàn thành (2026-09-07) · **Chặn bởi:** C, D · **Repo:** Elite

---

## 1. Vẽ chiến lược lên chart

Backtest đã có sẵn chuỗi: replay chiến lược trên `klines` → `compute_strategy_indicator_lines()`
→ `card.add_overlay_indicator(name, color, width)` + `card.update_indicator_data(name, x, y)`;
vùng xu hướng qua `compute_strategy_trend_zones()` → `card.set_script_regions(key, spans)`.
Task C đã đưa 2 hàm tính đó ra `components/strategy_overlay/`, nên màn Giao dịch dùng lại được
**nguyên xi** — quan trọng hơn: dùng chung một hàm nghĩa là **đường vẽ trên chart live và đường
vẽ trong backtest không thể lệch nhau**, thứ mà 2 bản cài đặt song song chắc chắn sẽ làm.

Vòng đời trên màn Giao dịch:

| Lúc nào | Làm gì |
| :--- | :--- |
| Nạp xong lịch sử nến | Replay toàn bộ → vẽ lần đầu |
| Nạp/gỡ chiến lược | Xoá đường cũ (`remove_indicator`) rồi vẽ lại theo chiến lược mới |
| Mỗi nến **đóng** | Replay lại trên buffer nến hiện có rồi đẩy `update_indicator_data` |
| Mỗi tick nến đang hình thành | **Không làm gì** — xem §1.1 |

**§1.1 — vì sao không vẽ theo tick.** `ChartCard` nhận tick liên tục; replay cả buffer mỗi tick là
O(N) mỗi lần, đúng loại chi phí `viewport_windowing.py` được sinh ra để tránh. Nến đóng ~1 lần/phút
ở `1m` là đủ: đường chỉ báo của chiến lược **chỉ đổi khi nến đóng** (`StrategyEngine.on_tick()` chỉ
nhận nến đã đóng — docstring của chính nó nói vậy), nên vẽ theo tick sẽ là vẽ thứ không có thật.

**§1.2 — dùng lại `throwaway strategy` như Backtest.** Không đọc trộm indicator state từ engine
đang chạy live: engine đó đang giữ trạng thái quyết định lệnh thật, mọi thứ đọc ra để vẽ phải là
một bản replay riêng, đúng cách `IndicatorCoordinator._throwaway_strategy` của Backtest đã làm.

## 2. Card TÍN HIỆU GẦN NHẤT

`StrategyEngine` **đã** publish `SignalGeneratedEvent` mỗi khi có tín hiệu khác HOLD — hiện không
ai ở tầng UI nghe. Thêm `SignalFeed` (`presentation/ui/common/signal_feed.py`) theo đúng khuôn
`OrderFeed`/`EquityFeed`, presenter subscribe, card hiện: hành động (MUA/BÁN/…), lý do
(`Signal.reason`), giá, giờ.

Giá trị thật của card này: hôm nay khi bot **không** đặt lệnh, user không có cách nào phân biệt
"chiến lược không ra tín hiệu" với "có tín hiệu nhưng bị chặn" — đúng nửa vấn đề `BUG-084` đã sửa
cho nhánh bị-chặn (`LiveOrderBlockedEvent`). Card này bịt nốt nửa còn lại.

## 3. Đổi theo file

- Mới `presentation/ui/common/signal_feed.py`.
- Mới `screens/trading/coordinators/strategy_overlay_coordinator.py` — giữ buffer nến, replay,
  đẩy lên `ChartCard`.
- `trading_presenter.py` — nối `SignalFeed`, gọi overlay coordinator ở 3 mốc ở bảng §1.
- `trading_view_model.py` / `trading_view.py` — card tín hiệu.

## 4. Test

- Overlay: nạp chiến lược ⇒ có đúng số đường mà `chart_line_colors()` khai báo; gỡ ⇒ đường bị xoá;
  nến đóng ⇒ `update_indicator_data` được gọi lại; **tick nến chưa đóng ⇒ KHÔNG gọi** (chốt §1.1).
- `SignalFeed`: publish `SignalGeneratedEvent` ⇒ card hiện đúng 4 trường.
