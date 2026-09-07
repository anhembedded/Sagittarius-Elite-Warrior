# EPIC-022 — Chiến lược sống trên màn Giao dịch: chọn, cấu hình, thấy nó trên chart

- **Trạng thái:** ✅ Hoàn thành (6/6 task con) — 2026-09-07
- **Ngày lập:** 2026-09-03
- **Tiền đề:** [`EPIC-021`](../EPIC-021_ket_noi_binance_futures_testnet/README.md) ✅ 13/13 —
  đường đi lệnh thật đã thông, nhưng phần "chạy chiến lược nào" bị cắt có chủ đích.

---

## 1. Vấn đề thật — user phát hiện bằng cách dùng, không phải đọc code

User mở màn Giao dịch và hỏi đúng một câu: **"sao không có ô chọn chiến lược? vậy nó chạy chiến
lược nào mà khớp?"**

Câu trả lời đo được từ code, và nó tệ hơn "thiếu một ô combobox":

| # | Phát hiện | Bằng chứng |
| :-: | :--- | :--- |
| **1** | Màn Giao dịch **không có control nào** cho chiến lược | `trading_view.py` (307 dòng) — grep "strategy" ra 0 widget |
| **2** | Chiến lược live chọn bằng **1 key config đọc lúc boot**, không sửa được từ UI | [`binance_bot_module.py:565-598`](../../../src/binance_bot_module.py) đọc `TRADING_LIVE_STRATEGY_KEY` rồi `build_engine(...)` **một lần duy nhất**, `MarketTickEventHandler` nhận 4 field **chỉ có trong constructor** |
| **3** | Giá trị key đó trong repo đang là **rỗng** | [`app_config.json:21`](../../../src/config/app_config.json) `"trading.live_strategy_key": ""` |
| **4** | ⇒ Bật giao dịch xong **không có gì chạy**, mà UI vẫn báo "Trading đang BẬT" | `market_tick_event_handler.py:86-91` — `strategy_engine is None` thì `return` im lặng |
| **5** | `build_engine` **có** nhận `params` nhưng boot không truyền | [`strategy_factory.py:15-20`](../../../src/application/services/strategy_factory.py) vs `binance_bot_module.py:580-584` |
| **6** | Không có cầu nối Strategy → chart | `EPIC-021I` §6.2 ghi thẳng: *"Không có cầu nối nào giữa 6 `Strategy` class và hệ `IndicatorScript`"* |

**Phát hiện 4 là một lỗi thành thật (truthful UI), không phải thiếu tính năng.**
`domain-truth-rule.md` §"Truthful Trading UI" cấm đúng chuyện này: *"Do not present a planned or
unsupported capability as available"*. Nút "Bật giao dịch" bật lên xanh trong khi hệ thống **biết
chắc** không có gì sinh tín hiệu — đó là UI nói dối, và trong bot giao dịch thì đó là tiền thật.

## 2. Cái đã có và tái dùng được — đừng viết lại

`EPIC-021I` §6.2 nói *"chưa có cơ chế backend nào để nối vào"*. Câu đó **đúng ở thời điểm đó**
nhưng nay đã sai một nửa — khảo sát lại cho thấy phần lớn cơ chế đã tồn tại, chỉ nằm sai chỗ
(khoá cứng trong màn Backtest) chứ không phải chưa có:

| Cần gì | Đã có sẵn | Vấn đề |
| :--- | :--- | :--- |
| Liệt kê 6 chiến lược | `StrategyRegistry.available()` | ✅ dùng thẳng |
| Dựng engine từ key + params | `build_engine(registry, key, publisher, params)` | ✅ dùng thẳng |
| Khai báo + validate thông số | `BaseStrategy.setup()` + `inputs` + ctor raise `ValueError` | ✅ dùng thẳng |
| Form thông số động theo metadata | `backtest/logic/bot_params_form.py` | ⚠️ **screen-agnostic nhưng nằm trong `screens/backtest/`** — import chéo màn hình bị cấm (`EPIC-021L`) |
| Widget 1 ô nhập thông số | `backtest_modals/_bot_param_field.py` | ⚠️ như trên, lại còn `_private` |
| Tính đường chỉ báo để vẽ | `backtest/logic/strategy_indicator_lines.py` | ⚠️ như trên |
| Tính vùng xu hướng để tô | `backtest/logic/strategy_trend_zones.py` | ⚠️ như trên |
| API vẽ lên chart | `ChartCard.add_overlay_indicator/update_indicator_data/set_script_regions` | ✅ dùng thẳng |
| Marker lệnh khớp trên chart live | `EPIC-021K` đã làm, key `_FILL_MARKERS_KEY` | ✅ đã chạy |
| Sự kiện tín hiệu | `SignalGeneratedEvent` do `StrategyEngine` publish sẵn | ✅ chỉ thiếu Feed |

**Kết luận thiết kế:** 4 dòng ⚠️ là **thăng cấp vị trí file**, không phải viết mới. Đúng
`architecture-rule.md` §5: một thư mục là một tầng, `screens/backtest/` không được là kho chứa
đồ dùng chung.

## 3. Mục tiêu — chuỗi thao tác user phải làm được

1. Mở màn Giao dịch → thấy card **CHIẾN LƯỢC** ở rail phải.
2. Chọn chiến lược trong 6 cái đang có (dùng chung registry với Backtest).
3. Mở **Thông số Chiến lược** → form sinh động theo đúng `input_*()` chiến lược đó khai báo,
   sai thì báo lỗi ngay, không nuốt.
4. Chọn khung thời gian giao dịch + % vốn/lệnh + đòn bẩy.
5. Bấm **Nạp chiến lược** → engine dựng lại (indicator state sạch), chart vẽ ngay đường chỉ báo
   + vùng xu hướng của chính chiến lược đó.
6. Bật giao dịch → **chỉ bật được khi đã nạp chiến lược**; nếu chưa, nút báo đúng lý do.
7. Khi có tín hiệu → card **TÍN HIỆU GẦN NHẤT** hiện hành động/lý do/giá/giờ, rồi marker lệnh
   khớp hiện trên chart (đường đã có sẵn từ `EPIC-021K`).
8. Đóng app mở lại → cấu hình còn nguyên, **nhưng không tự nạp, không tự bật** (bài học
   `BUG-101`/`BUG-104`).

**Ngoài phạm vi, cố ý:** nút Huỷ lệnh/Đóng vị thế thủ công (cần `CancelOrderCommand`/
`ClosePositionCommand` + method mới trên port `ITradingClient` + adapter — user đã chọn không
làm lượt này); giao dịch nhiều symbol/nhiều khung cùng lúc (`BUG-085` — 1 engine 1 symbol 1
khung, cố ý).

## 4. Hai quyết định an toàn, ghi ở đây để không bị suy diễn lại

**4.1 — Không cho đổi chiến lược khi giao dịch đang BẬT.**
Đổi engine giữa chừng nghĩa là indicator state bị vứt và dựng lại trong khi một vị thế đang mở:
chiến lược mới không biết gì về lệnh vào đã có, và tín hiệu thoát của chiến lược cũ sẽ không bao
giờ tới. Đây là "collapsing trading semantics" đúng nghĩa `domain-truth-rule.md`. `ArmStrategy`
trả về block reason `TRADING_IS_ENABLED`, không âm thầm cho qua.

**4.2 — Không cho bật giao dịch khi chưa nạp chiến lược.**
Thêm `EnableTradingBlockReason.NO_STRATEGY_ARMED`, kiểm **trước** 2 vòng gọi mạng (rẻ và thành
thật hơn). Đây là phần sửa phát hiện #4 ở §1.

## 5. Danh sách task con — xếp theo rủi ro tăng dần

| # | Task | Chặn bởi | Trạng thái |
| :-: | :--- | :--- | :---: |
| **A** | [`LiveStrategySession` — chiến lược đổi được lúc chạy, thay cho 4 field đóng băng lúc boot](completed/EPIC-022A_live_strategy_session.md) | — | ✅ |
| **B** | [2 rào an toàn: chưa nạp thì không bật, đang chạy thì không đổi](completed/EPIC-022B_rao_an_toan_arm_va_enable.md) | A | ✅ |
| **C** | [Thăng cấp form thông số + tính toán overlay ra khỏi `screens/backtest/`](completed/EPIC-022C_thang_cap_thanh_phan_dung_chung.md) | — (song song được) | ✅ |
| **D** | [UI: card CHIẾN LƯỢC + dialog Thông số Chiến lược trên màn Giao dịch](completed/EPIC-022D_ui_chon_chien_luoc.md) | A, B, C | ✅ |
| **E** | [Vẽ chiến lược lên chart live + card TÍN HIỆU GẦN NHẤT](completed/EPIC-022E_ve_chien_luoc_len_chart_live.md) | C, D | ✅ |
| **F** | [Nhớ cấu hình giữa các phiên — không tự nạp, không tự bật](completed/EPIC-022F_nho_cau_hinh_giua_cac_phien.md) | D | ✅ |

> **Bug sinh ra từ epic này, đã đóng:**
> [`BUG-107`](../../bug_report/completed/BUG-107_arm_strategy_button_calls_a_tracker_method_that_never_existed.md)
> (2026-09-07) — nút "Nạp chiến lược" của **D** gọi `ActionOwnershipTracker.start_action()`, một
> method chưa từng tồn tại (API thật là `begin_action(kind, config, previous_state)`), nên mọi lần
> bấm đều `AttributeError` trước cả dòng logic đầu tiên. Lọt qua được vì `mypy` loại toàn bộ
> `src/presentation/` và vì 12 test của card đều gọi `arm()` — method **nằm dưới** nút — chứ chưa
> test nào chạm `on_arm_clicked()`. Đã bổ sung 5 test đi qua đúng entry point của nút.
