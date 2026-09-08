# BUG-034 — Dev Board Live Chart: giá nến không hiển thị, trục Y bị auto-range sai thang đo

**Reported date:** 2026-08-23
**Severity:** 🟠 **P2**
**Status:** 🔴 **MỞ LẠI 2026-09-08** — đóng buổi sáng rồi mở lại ngay trong ngày: user yêu cầu
"thêm log vào những nơi cần thiết xem có tái hiện được không", và **tái hiện được**. §10 là lượt
điều tra 5: tìm ra **vì sao 4 lượt trước không tái hiện được** (một điểm mù của môi trường
headless, không phải bug khó), và dựng lại được **đúng hình dạng triệu chứng** trong test tự động.
4 lượt trước (2026-08-23, 08-26, 08-30, 08-31). Đã loại trừ 7 giả thuyết (indicator overlay sai thang,
`DevIndicatorScript` vẽ RSI/MACD lên plot giá, subplot rò dữ liệu, kline map sai thang,
`autorange=[False, 1.0]` là bug, trend-zone shading, marker Buy/Sell/Overbought) — 3 giả thuyết
cuối loại trừ bằng đối chiếu source `pyqtgraph` thật, không suy đoán.

**⚠️ §9 (quyết định đóng) đã bị §10 thay thế.** Giữ lại §9 nguyên văn vì nó ghi đúng trạng thái
hiểu biết tại thời điểm đó — và vì nó là ví dụ tốt cho chuyện "đóng vì không tái hiện được" có thể
sai chỉ sau một lượt điều tra nữa.

---

## 1. Hiện tượng (Symptom)

Trên màn hình **Dev Board**, sau khi bấm "Start Live" cho symbol `ETHUSDT` (khung `1m`),
luồng dữ liệu live khởi động thành công (xem log bên dưới) nhưng **vùng vẽ nến chính của
biểu đồ trống hoàn toàn** — không thấy thân nến/wick nào, dù dữ liệu giá đang chảy vào đúng.

Ảnh chụp màn hình do người dùng cung cấp cho thấy:

- Panel "Developer Board (Live...)" bên phải hiển thị symbol `ETHUSDT`, giá hiện tại
  `2,425.x` (góc trên bên phải).
- Toolbar chart chọn khung `1m` (đã bấm sáng).
- Dòng đọc OHLC ở crosshair phía trên chart: `08-22 08:15:59  O 2439.8200 H 2440.1600
  L 2439.4500 C 2440.0700 (+0.01%)` — các giá trị này nằm đúng vùng giá ETH thật (~2400),
  có vẻ hợp lý.
- 4 đường EMA (`ema_20`, `ema_50`, `ema_100`, `ema_200`) hiển thị trong legend với giá trị
  cũng nằm đúng vùng ~2420–2437 — hợp lý.
- **Tuy nhiên trục Y của chart chính lại hiện thang đo `-50, 0, 50, 100`** — hoàn toàn không
  khớp với vùng giá ~2400 mà OHLC/EMA đang báo. Không có thân nến nào hiển thị được trong
  vùng plot chính (khoảng giữa 4 đường EMA và biểu đồ volume phía dưới trống trơn, chỉ có nền
  đen).
- Có 1 đường kẻ ngang đứt nét kèm nhãn giá trị `12.6405` xuất hiện giữa chart — con số này
  cũng không khớp với bất kỳ ngữ cảnh giá/thang đo nào đang hiển thị.
- Biểu đồ **volume** ở dưới cùng (thang `0–500`) có vẻ vẫn vẽ bar bình thường, không trống.
- Panel "System Monitor" (log) bên phải cho thấy chuỗi khởi động Live Stream **hoàn tất bình
  thường, không có lỗi/exception nào được log**:

```text
[16:16:03] System Health: HEALTHY (DB: OK, Container: OK, EventBus: OK)
[00:47:44] Starting Live Stream (Auto-Sync)...
[00:47:45] Prepared 1 charts.
[00:47:45] Syncing missing data from Binance...
[00:47:56] Reloading historical data onto charts...
[00:47:56] Refreshed 2000 historical klines for ETHUSDT.
[00:47:56] Opening Websocket stream...
[00:47:56] Live stream for ['ETHUSDT'] is running.
[00:48:00] [Live] ETHUSDT candle closed at 2425.11.
```

(Lưu ý: dòng `[16:16:03]` và các dòng `[00:47:xx]`/`[00:48:00]` không cùng một mốc thời gian
thực — có thể là 2 phiên/2 lần khởi động khác nhau bị gộp trong cùng khung log hiển thị, hoặc
đơn giản là đồng hồ hiển thị theo giờ khác nhau. Ghi lại nguyên văn, không diễn giải thêm.)

## 2. Ảnh chụp màn hình

Người dùng đã cung cấp ảnh chụp trực tiếp trong hội thoại (không có file lưu sẵn trên đĩa để
đính kèm vào report này) — mô tả chi tiết ở mục 1 dựa trên đúng nội dung ảnh đó.

## 3. Kỳ vọng (Expected)

Trục Y của chart chính phải auto-range theo đúng vùng giá thực của nến đang vẽ (ví dụ ~2400
cho ETHUSDT), và thân nến phải hiển thị được trong vùng plot — giống cách chart hoạt động ở
màn hình Backtest.

## 4. Lượt điều tra 1 (2026-08-23) — chưa ra root cause, nhưng đã loại trừ được 4 giả thuyết

**Trạng thái: vẫn Open.** Ghi lại để lượt sau không làm lại từ đầu.

### Đã loại trừ, kèm bằng chứng

| # | Giả thuyết | Kết quả | Bằng chứng |
| :--- | :--- | :--- | :--- |
| 1 | Indicator thang dao động bị vẽ `overlay` lên plot giá, kéo auto-range | ❌ Sai | `macd_full_script.py` và `rsi_14_script.py` đều `overlay = False`; `IndicatorScriptRunner` gán `overlay=script.overlay` đúng ở cả 2 chỗ (dòng 146, 162) rồi rẽ `add_overlay_indicator`/`add_subplot_indicator` theo đúng cờ đó |
| 2 | `DevIndicatorScript` (`overlay=True`, chạy trên Dev Board) vẽ RSI/MACD lên plot giá | ❌ Sai | Nó *khai báo* `rsi(14)`/`macd()`/`level(70)` nhưng chỉ dùng cho điều kiện/marker. Toàn bộ lệnh `plot()` của nó là `EMA 12`, `EMA 26`, `WMA 20`, `close + session_range` — đều thang giá |
| 3 | `add_subplot_indicator` rò dữ liệu subplot sang plot chính | ❌ Sai | `IndicatorManager.add_subplot()` tạo `PlotItem` riêng qua `_plot_layout.add_subplot()` rồi mới `plot()` lên đó |
| 4 | Dữ liệu nến bị map sai thang | ❌ Sai | `kline_mapping.map_klines()` lấy thẳng `open/high/low/close_price`, không chia/nhân gì |

### Probe tái hiện — đường đi bình thường HOÀN TOÀN ĐÚNG

Dựng `ChartCard` thật, lặp lại đúng chuỗi Dev Board (2000 nến ETH ~2425 → volume →
4 EMA overlay → RSI subplot 0–100 → MACD subplot ±45), in dải Y sau từng bước:

```
0. chưa có data                    Y=[0.00, 1.00]
1. sau render_historical_data      Y=[2408.96, 2442.34]
2. sau render_historical_volume    Y=[2408.96, 2442.34]
3. sau 4 EMA overlay               Y=[2408.96, 2442.34]
4. sau subplot rsi_14 (0..100)     Y=[2408.76, 2442.54]
5. sau subplot macd (-45..45)      Y=[2406.28, 2442.87]
```

Y bám đúng ~2425 xuyên suốt; **subplot không hề rò sang plot chính**. Đáng chú ý: dải
mặc định khi chưa có data là `[0, 1]`, **không phải** `-50..100` — nên `-50..100` không
đến từ trạng thái "plot rỗng".

### Ghi chú đọc lại triệu chứng

- Con số `12.6405` có **đúng 4 chữ số thập phân**, khớp format `f"{name}: {y[-1]:.4f}"` của
  legend (`IndicatorManager.update_data`) và cũng khớp nhãn crosshair. **Không nên coi nó là
  giá trị của một indicator** cho tới khi có bằng chứng khác.
- Vì subplot RSI/MACD (nếu bật) nằm **giữa** plot chính và volume, có khả năng dải
  `-50..100` nhìn thấy trong ảnh là trục của *subplot đó*, còn plot chính thì rỗng và bị
  ép mỏng. Chưa xác nhận được — cần ảnh/log của đúng lần tái hiện.

### Đã làm để lượt sau tự chẩn đoán được

Dòng log `[chart-data]` sẵn có trong `ChartCard.render_historical_data()` trước đây chỉ
ghi số nến + **x-range** — không đủ để phân biệt hai khả năng hoàn toàn khác nhau:
"data không tới card này" và "data tới rồi nhưng range bỏ qua nó". Đã bổ sung vào **chính
dòng đó** (không thêm dòng mới, không thêm nhiễu):

- `price [min_low, max_high]` — thang giá mà dữ liệu thật sự mang
- `y-range [min, max]` — dải mà view thật sự lấy
- `autorange=[x, y]` — auto-range còn bật không

```
[chart-data] ChartCard(ETHUSDT): loaded 2000 candles spanning [...]
| price [2408.0137, 2441.9807] | initial view x-range [...]
| y-range [2406.4262, 2443.5681] | autorange=[False, True] | chart type=candlestick
```

## 5. Suggested next steps

1. **Tái hiện với `--debug`** rồi `grep '\[chart-data\]' logs/debug-*.log`. Ba khả năng,
   dòng log phân biệt được ngay:
   - `loaded 0 candles` → data không tới card đang hiển thị (nghi vấn re-key card ở
     `_ensure_chart_cards`).
   - `price [~2400]` nhưng `y-range [-50, 100]` → range bỏ qua data; đào tiếp
     `_set_initial_view_range()` / `_apply_view_bounds()`.
   - `autorange=[..., False]` → auto-range Y đã bị tắt ở đâu đó.
2. Chụp lại ảnh **kèm cả vùng subplot**, để xác nhận `-50..100` là trục của plot chính hay
   của subplot RSI/MACD.
3. Chỉ sau khi có 1 hoặc 2 mới viết regression test — hiện chưa biết đủ để test đúng chỗ.

## 6. Lượt điều tra 2026-08-26 — thêm 1 giả thuyết **được xác nhận thật** (không phải bị loại),
nhưng **không đóng được bug này**

**Trạng thái: vẫn Open.** Dựng lại đúng chuỗi Dev Board (real `ChartCard`, real
`IndicatorScriptRunner`, real `dev_showcase`+`rsi_14`+`macd_full`, 2000 nến tổng hợp) headless
trên Linux (`QT_QPA_PLATFORM=offscreen`, không cần Binance thật) để tự động hoá bước 1–2 ở trên
mà không cần máy Windows/GUI thật. Kết quả:

- **Y-range của main plot bám đúng theo dữ liệu tổng hợp** (không tái hiện được `-50..100`) — dữ
  liệu tổng hợp tự nó là random walk không có mean-reversion nên trôi giá hợp lệ, không phải bug.
  Nghĩa là: hạ tầng auto-range mô tả ở §4 (main plot chỉ nhận đúng item của chính nó) **vẫn đúng**
  với cấu hình được thử — giả thuyết "range bỏ qua data" (bước 1, gạch 2) **chưa được xác nhận**
  bằng repro này.
- Nhưng: phát hiện một defect **thật, khác, đã xác nhận** trong cùng subsystem — `macd_full`
  (3 line: MACD/Signal/Histogram) tạo **3 subplot row riêng** thay vì 1 row chung, khiến main
  plot bị ép chỉ còn ~3/8 chiều cao khi bật MACD, và crosshair bị đăng ký trùng. Đã tách hồ sơ
  riêng: [`BUG-053`](../completed/BUG-053_multi_line_subplot_script_gets_one_row_per_line.md) —
  root-caused, regression-tested (red→green), **đã sửa và đóng**.
- **Vì sao BUG-053 không đóng được BUG-034 này:** repro headless ở trên đã bật đúng tổ hợp script
  Dev Board đã dùng (dev_showcase + rsi_14 + macd_full) và chạy qua đúng `IndicatorScriptRunner`
  thật — nếu việc ép main plot xuống 3/8 chiều cao đã đủ để tạo ra đúng triệu chứng "-50..100 +
  candle rỗng", repro này lẽ ra phải lộ ra dấu hiệu bất thường trong Y-range hoặc x-range. Nó
  không lộ. Nên khả năng cao nhất: BUG-053 là một defect thật, đáng sửa độc lập, nhưng **không
  phải** cơ chế duy nhất (có thể không phải cơ chế nào) tạo ra triệu chứng BUG-034 đã báo.
- **Việc còn thiếu, không đổi so với §5:** vẫn cần ảnh chụp thật + log `--debug` từ một lần tái
  hiện sống (GUI thật hoặc Binance thật) — headless repro chỉ dựng lại được *cấu trúc* wiring, không
  dựng lại được bất cứ thứ gì phụ thuộc timing thật (live tick xen giữa `render_historical_data()`
  và lúc script subplot được tạo, thứ tự Qt event loop, DPR/backend thật). Bước 1–2 ở §5 **vẫn còn
  nguyên giá trị**, chưa bước nào trong đó được thực hiện bằng phiên này.

## 7. Lượt ghi nhận hiện tượng sống 2026-08-30 — log thực tế tái hiện đúng y-range bất thường

Trong phiên chạy live ngày 2026-08-30 trên Dev Board với symbol `0GTRY` (khung `1m`), log hệ thống ghi nhận bằng chứng sống:

```text
2026-08-30 17:32:18,341 - App.ChartCard - INFO - [chart-data] ChartCard(0GTRY): loaded 2000 candles spanning [1787965920.0, 1788085860.0] | price [7.6760, 8.1730] | initial view x-range [1788081290.0, 1788081490.0] | y-range [-71.3690, 46.1465] | autorange=[False, 1.0] | chart type=candlestick
```

**Đối chiếu với các giả thuyết ở §5:**
- `price [7.6760, 8.1730]`: dữ liệu nến thực tế có giá quanh 7.6..8.2.
- Nhưng `y-range` bị gán dải âm/dương cực rộng: **`[-71.3690, 46.1465]`**.
- Dải giá thực (chiều cao ~0.5) chiếm chưa tới 0.5% dải trục Y (chiều cao ~117.5), giải thích vì sao nến biến mất hoặc bị ép thành đường thẳng phẳng lì trên màn hình.
- Ngoài ra `autorange=[False, 1.0]` thay vì `[False, True]` — giá trị `1.0` bất thường ở vị trí boolean auto-range Y là đầu mối quan trọng cho lượt điều tra tiếp theo.

## 8. Lượt điều tra 2026-08-31 — 3 giả thuyết mới bị loại trừ bằng đối chiếu source pyqtgraph thật

**Trạng thái: vẫn Open.** Không có máy Windows/GUI thật hay Binance thật trong môi trường phiên
này để tái hiện sống — không đoán fix khi chưa có bằng chứng, chỉ thu hẹp thêm không gian nghi
vấn bằng cách đọc thẳng source `pyqtgraph` (cài `pyqtgraph` thật trong venv, đọc
`ViewBox.py`/`LinearRegionItem.py`, không suy đoán từ trí nhớ).

### 8.1. `autorange=[False, 1.0]` (đầu mối §7) — KHÔNG phải bug, đóng hẳn thread này

Đọc `pyqtgraph/graphicsItems/ViewBox/ViewBox.py::enableAutoRange()`:

```python
if enable is True:
    enable = 1.0
```

`ViewBox.autoRangeEnabled()` trả thẳng `self.state['autoRange'][:]` — nên `[False, 1.0]` **chính
là** cách pyqtgraph tự biểu diễn `[False, True]` nội bộ, xảy ra với **MỌI** chart, MỌI symbol, bất
kể có bug hay không. Đầu mối này ở §7 (đánh dấu "quan trọng cho lượt điều tra tiếp theo") là
**đường cụt** — Y auto-range vẫn đang **bật** ở lần tái hiện đó, không phải bị tắt/hỏng. Câu hỏi
thật vẫn là: auto-range **bật** nhưng tính ra dải sai — tại sao.

### 8.2. `RegionLayer` (trend-zone shading, `self.shade()`) — loại trừ, có bằng chứng

`region_layer.py:87` gọi `self._plot.addItem(item)` **không** có `ignoreBounds=True` — trông đáng
ngờ thoạt nhìn. Nhưng đọc `LinearRegionItem.dataBounds(axis)`:

```python
def dataBounds(self, axis, frac=1.0, orthoRange=None):
    if axis == self._orientation_axis[self.orientation]:
        return self.getRegion()
    else:
        return None
```

`orientation` mặc định là `'vertical'` (đúng cách `_create_item` khởi tạo, không truyền
`orientation`) → trục tương ứng là X, nên `dataBounds(1)` (trục Y) trả `None` — `ViewBox` loại nó
khỏi phép tính auto-range Y bất kể có bao nhiêu span. **Không phải nguồn gây lỗi.**

### 8.3. `MarkerLayer` (Buy/Sell/Overbought/Strong) — loại trừ, có bằng chứng

`TriangleMarkerItem` (`marker_layer.py:22`) kế thừa `QGraphicsPathItem` (Qt thuần), **không**
implement `dataBounds`. Đọc `ViewBox.childrenBounds()`:

```python
if hasattr(item, 'dataBounds') and item.dataBounds is not None:
    ...
```

Item không có `dataBounds` bị loại thẳng khỏi vòng lặp tính bounds — dù `configure()` gọi
`setPos(x, y)` với `y` là giá trị marker thật (`fast`/`close`/`high_price`), vị trí đó **không
bao giờ** được `ViewBox` đọc để auto-range. **Không phải nguồn gây lỗi**, kể cả nếu `y` từng là
giá trị sai.

### 8.4. Còn lại — thu hẹp về đúng các `PlotDataItem` giá thật

Sau §8.2/8.3, danh sách item CÓ tham gia auto-range Y chỉ còn: nến (candlestick), volume bar,
và các đường overlay từ `self.plot()` (EMA 12/26, WMA 20, "Widening band" = `close +
session_range`). Cả 4 đều đã đọc code ở §4 lượt trước và xác nhận chỉ dùng giá trị thang giá
thật — không tìm thêm được nghi vấn tĩnh mới ở đây. `"Widening band"` là biểu thức duy nhất có
phép cộng (`close + session_range`) thay vì gán thẳng 1 field — nếu `session_range` từng là
`NaN`/`inf` (ví dụ `high_price`/`low_price` bất thường từ 1 tick lỗi) sẽ tạo giá trị bất
thường, nhưng **chưa có bằng chứng** `high_price`/`low_price` từng sai — cần log giá trị nến thô
tại đúng bar gây lỗi để xác nhận, không đoán.

### 8.5. Vì sao vẫn chưa đóng được

Không có môi trường Windows/GUI thật hoặc kết nối Binance thật trong phiên này để tái hiện sống
theo đúng "Suggested next steps" §5 (chụp `--debug` log lúc lỗi xảy ra thật). Headless repro với
dữ liệu tổng hợp (§6) đã chứng minh không tái hiện được — nghi vấn còn lại phụ thuộc timing live
tick thật hoặc hình dạng dữ liệu của 1 symbol/tick cụ thể (`0GTRY` ở §7), không dựng lại được
bằng dữ liệu giả lập ngẫu nhiên. Việc cần làm tiếp không đổi so với §5 bước 1–2 — chưa bước nào
làm được vì thiếu môi trường, không phải vì thiếu hướng đi.


---

## 9. Đóng hồ sơ 2026-09-08 — user quyết định dừng điều tra

**Đóng vì hết đường đi trong môi trường có sẵn, KHÔNG phải vì lỗi không tồn tại.** Ghi rõ vì hai
chuyện đó dẫn tới hai hành động rất khác nhau nếu triệu chứng quay lại.

### 9.1. Cái ĐÃ được chứng minh

§7 là **log sản xuất thật**, không phải suy đoán:

```text
[chart-data] ChartCard(0GTRY): ... | price [7.6760, 8.1730] | y-range [-71.3690, 46.1465] | ...
```

Dải giá thật cao ~0,5 đơn vị nằm trong một trục Y cao ~117,5 đơn vị — nến bị ép dẹp tới mức biến
mất. Đây là hành vi sai, đã xảy ra, đã ghi lại. Đóng hồ sơ **không** đảo ngược điều đó.

### 9.2. Cái KHÔNG được chứng minh, và vì sao dừng

Cơ chế gây ra nó. Bốn lượt điều tra loại trừ được 7 giả thuyết nhưng không tới được nguyên nhân,
và mọi hướng còn lại (§8.4) đều cần **tái hiện sống trên Windows/GUI thật hoặc Binance thật** —
thứ không có trong môi trường phát triển của repo này. Headless repro với dữ liệu tổng hợp đã thử
và không tái hiện được (§6).

Bốn lượt đã dừng ở cùng một chỗ vì cùng một lý do, và lý do đó không đổi được từ bên trong repo.
Giữ hồ sơ mở thêm chỉ làm cột "Đang mở" của Bug Board báo một việc mà không ai bắt đầu được. Nên:
đóng, giữ nguyên toàn bộ bằng chứng.

### 9.3. Nếu triệu chứng quay lại — công cụ chẩn đoán ĐÃ nằm sẵn trong code

Đây là lý do đóng hồ sơ này rẻ hơn nó có vẻ. Lượt điều tra 1 (§4) đã bổ sung vĩnh viễn vào dòng
log `[chart-data]` của `ChartCard.render_historical_data()` ba trường: `price [min, max]`,
`y-range [min, max]`, `autorange`. Chính ba trường đó là thứ đã bắt được bằng chứng §7.

Nghĩa là **không cần mở lại hồ sơ để bắt đầu chẩn đoán** — chỉ cần chạy với `--debug` rồi
`grep '\[chart-data\]' logs/debug-*.log` là có ngay dữ kiện. Việc còn thiếu vẫn đúng như §5
bước 1–2: một lần tái hiện sống có ảnh chụp **kèm vùng subplot** + log của đúng lần đó.

### 9.4. Nếu mở lại

Mở **hồ sơ mới**, tham chiếu ngược file này; đừng sửa lại file đã đóng. Bắt đầu từ §8.4 (danh sách
nghi vấn đã thu hẹp còn các `PlotDataItem` thang giá thật, trong đó `"Widening band"` =
`close + session_range` là biểu thức duy nhất có phép cộng và là chỗ `NaN`/`inf` có thể lọt vào) —
đừng làm lại 7 giả thuyết đã loại trừ.


---

## 10. Lượt điều tra 5 (2026-09-08) — **tái hiện được**, và tìm ra vì sao 4 lượt trước không

**Trạng thái: MỞ LẠI.** §9 đóng hồ sơ này sáng cùng ngày với lý do "không tái hiện được từ môi
trường hiện có". Lý do đó **sai** — không phải vì thiếu môi trường, mà vì cả 4 lượt trước đo sai
thời điểm.

### 10.1. Điểm mù: pyqtgraph **không** tính lại auto-range lúc thêm item

`ViewBox` chỉ **đánh dấu view bẩn** khi có item mới, rồi tính lại ở lần **paint** kế tiếp. Trên
`offscreen` không có paint nào xảy ra, nên `viewRange()` đọc ngay sau `render_historical_data()`
trả về dải **trước khi** indicator được thêm — tức là dải *khoẻ mạnh*.

Đó chính xác là điều §4 và §6 đã đo và kết luận "Y bám đúng ~2425 xuyên suốt". Phép đo đúng; kết
luận rút ra từ nó thì không. Ép một lượt tính lại (`vb.updateAutoRange()`, đúng thứ paint thật sẽ
làm) là thấy ngay:

```
--- sau render_historical_data (2000 nến, giá ~8)
      y-range [7.1448, 8.0552]                       ← khoẻ, và 4 lượt trước dừng ở đây
--- sau khi thêm 1 overlay thang dao động (10..90) lên main plot
      y-range [7.1448, 8.0552]                       ← VẪN khoẻ: chưa paint, chưa tính lại
--- sau vb.updateAutoRange()  (thứ paint thật sẽ chạy)
      y-range [2.5061, 95.1570]                      ← nến ~8 bị nén còn 0,9% trục
```

**Đây là hình dạng triệu chứng đã báo**: giá đúng, trục Y sai thang, nến biến mất.

### 10.2. Cơ chế

Trục Y của main plot **dùng chung** cho mọi item trên nó. Một series **không theo thang giá** nằm
trên main plot sẽ kéo auto-range ra và ép nến thành một vạch. Ứng viên: một script có
`overlay = True` mà vẽ đường dao động (`overlay` là cờ **theo script**, không theo từng đường —
xem `IndicatorScriptRunner`), một đường `level()`, hoặc một curve còn sót từ symbol trước.

**Chưa chứng minh được** đây là thứ đã xảy ra trong phiên `0GTRY` ở §7: 3 script Dev Board đang
ship (`dev_showcase`/`rsi_14`/`macd_full`) đều đã kiểm ở §4 và không vẽ đường sai thang lên main
plot. Nên §10 chứng minh **cơ chế**, không chứng minh **thủ phạm cụ thể** của §7.

### 10.3. Đã thêm: log tự chỉ đích danh thủ phạm

`ChartCard._report_squashed_price_band()` gắn vào `vb.sigRangeChanged` — **không** đặt cuối
`render_historical_data()`, đúng vì lý do §10.1: phải nghe lúc dải *thật sự chốt*, không phải lúc
nạp xong.

Bắn **1 dòng WARNING duy nhất cho mỗi lần bất thường** (`logging-rule.md` §4 — pan/zoom bắn signal
này liên tục), và chỉ khi dải giá **nằm trong** view mà chiếm dưới `_PRICE_BAND_MIN_VIEW_FRACTION`
(20%) — điều kiện "nằm trong" loại đúng cái transient `[0, 1]` mà mọi lần nạp bình thường đều đi
qua. Nội dung: **Y bounds của từng item trên main plot, kèm tên đăng ký của nó**:

```
[chart-range] ChartCard(0GTRY): price band [7.1917, 8.0083] fills only 0.88% of
y-range [2.5061, 95.1570] — candles are unreadable. Y bounds each item on the main
plot claims: FastCandlestickItem=[7.1917, 8.0083] PlotDataItem=None rsi_14=[10.0000, 90.0000]
```

`rsi_14=[10.0000, 90.0000]` là câu trả lời mà 4 lượt trước không có. `IndicatorManager.name_of()`
là phần thêm để có được cái tên đó — "một `PlotDataItem` khai [10, 90]" bắt người đọc đi tìm, còn
"`rsi_14` khai [10, 90]" thì không.

### 10.4. Test giữ lại

`tests/unit/presentation/ui/components/test_chart_card.py`, 3 test:

| Test | Ghim cái gì |
| :--- | :--- |
| `test_auto_range_does_not_settle_until_the_view_is_asked_to_update` | Chính điểm mù §10.1, viết thành một sự thật về môi trường — để người sau viết repro chart-range không rút lại đúng kết luận sai đó từ một probe xanh |
| `test_a_non_price_series_on_the_main_plot_squashes_the_candles` | Triệu chứng + log **nêu đích danh** series gây ra (assert vào tên, không phải vào "dải sai" — "dải sai" là thứ hồ sơ đã có suốt 4 lượt mà không hành động được) |
| `test_a_healthy_chart_reports_nothing` | Lần nạp bình thường phải im lặng, nếu không log này thành nhiễu rồi bị lọc bỏ |

Mutation-verify đã làm thật: đặt `_PRICE_BAND_MIN_VIEW_FRACTION = 0.0` → test squash đỏ đúng lý
do → revert.

### 10.5. Việc còn lại

§5 bước 1–2 **vẫn còn nguyên giá trị**, nhưng giờ rẻ hơn hẳn: một lần tái hiện sống chỉ cần
`grep '\[chart-range\]' logs/debug-*.log` là có tên item thủ phạm, không cần ảnh chụp kèm subplot
để đoán nữa. Nếu dòng đó **không** xuất hiện trong khi nến vẫn biến mất, thì cơ chế §10.2 bị loại
và nghi vấn quay về §8.4.
