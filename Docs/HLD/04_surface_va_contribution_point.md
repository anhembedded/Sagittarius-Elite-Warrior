# §4 — Surface và contribution point

## 4.1 Vấn đề cần giải — đo được

Trading (`screens/trading`) và Dev Board (`screens/dashboard`) cùng dựng **một** nghiệp vụ: 59 tên
method/thành viên trùng; cùng `PositionsPanel`, `OpenOrdersPanel`, cùng recipe equity chart (comment
tự ghi *"same construction recipe"*), strategy card cùng 8 objectName, session card/last-signal card
docstring tự ghi *"mirrors"*. `DashboardPresenter` 2.008 dòng, `TradingPresenter` 973 dòng.

User chốt (ADR D4): Trading = màn use-case thật; Dev Board = màn developer để **test** và **khám phá
API**; *"nên có nhiều cái tụi nó sẽ trùng lặp"* — trùng là **đúng ý**, nhưng phải trùng bằng **một**
widget dùng hai chỗ, không phải hai bản chép.

## 4.2 Surface — màn hình không có nghiệp vụ

**Surface** = một screen ở `shell/surfaces/<id>/` chỉ làm 3 việc: (1) bố cục (`PageShell` +
slot), (2) hỏi `IContributionRegistry` "ai góp gì vào slot nào của tôi", (3) dựng widget qua factory
module góp. **0 dòng nghiệp vụ, 0 Coordinator nghiệp vụ, 0 Feed** — mọi thứ đó nằm trong widget do
module sở hữu.

| Surface | Slot | Gate | Route mặc định |
| :--- | :--- | :--- | :--- |
| `trading` | `header` · `context_bar` · `workspace` (chart) · `rail` (card) · `console` | luôn | ✅ **mặc định** 🔵 (hôm nay Dev Board là `is_default=True`) |
| `dev_board` | `header` · `system_controls` · `workspace` (nhiều chart) · `rail` · `probes` 🔵 · `console` | **`dev.mode`** 🔵 (hôm nay **không gate**, đo `dev.mode` chỉ dùng cho asset validator, log filter, FPS overlay) | không |
| `settings` | `sections` | luôn | không |

⚠️ Hai thay đổi hành vi **nhìn thấy được** (không phải refactor thuần): route mặc định → Trading;
Dev Board ẩn khi `dev.mode=false`. Ghi ở đây để user biết trước; cả hai đảo được bằng một dòng config.

**Widget góp vào surface = của module.** Ví dụ `trading` góp `PositionsPanel` factory vào
`trading.rail` **và** `dev_board.rail` — cùng một class, hai instance, một `LiveOrderBookCoordinator`
(trong `modules/trading/ui/`). Trùng lặp = 0 vì không còn gì để chép.

## 4.3 Contribution point — kind vòng 1 (❓ O1: schema cuối chốt vòng 2)

Cơ chế: module khai báo **mô tả** (descriptor, frozen dataclass) + factory; surface/shell render.
Nguyên tắc mượn từ Engine `EPIC-001D`: *"Python describes, QML renders"*, *"registry là cho bề mặt thật
sự động"*, *"regions decide geometry"*.

| Kind | Descriptor (nháp) | Ai góp | Ai render | Thay cho hôm nay |
| :--- | :--- | :--- | :--- | :--- |
| `screen` | `route, title, icon, section_key, sequences, is_default, factory(container) -> (View, Presenter)` | mọi module | shell (`ScreenRegistry` ✅ `EPIC-016` — giữ tới Phase 5) | tuple hard-code 5 module `app_bootstrapper.py:322` |
| `surface_widget` | `surface_id, slot, order, factory(container) -> QWidget, owner_module` | market_data, trading, strategy, charting, indicators | surface | 2 Presenter tự dựng card |
| `settings_section` | `title, order, factory(container) -> QWidget` (form bound tới config key **của module**) | trading (venue, credentials-check, limits), market_data (venue, default symbols/interval/sync days), ui_kit (theme) | surface `settings` | `SettingsView` 1 grid biết mọi config key |
| `dev_probe` 🔵 | `title, module_id, factory(container) -> QWidget` | bất kỳ module có API sàn chưa rõ | surface `dev_board.probes`, chỉ khi `dev.mode` | **chưa có gì** (đo: không probe/raw-endpoint UI nào trong app) |
| `cli_command` | `name, build_parser(sub), execute(app, args)` | market_data (`sync`,`stream`), trading (`exchange-status`,`order-preview`,`order-dry-run`), strategy (`trade-once`) | `shell/cli` | `main.py:139-156` if/elif + `cli_commands.json` |
| `status_tile` | `key, factory -> QWidget` | trading (WS pill), market_data (price ticker) | surface header | `DevBoardPanel.header_actions` |

**Cân nhắc, không nhận vòng 1:** `chart_overlay` — vẽ lên chart đi qua `IChartHost` (port của
`support/charting`) do surface đưa cho widget; chưa cần registry riêng. `health_tile` — gộp vào `status_tile`.

## 4.4 `dev_probe` — "discover API" là gì, cụ thể

User: *"khi bạn dev nếu API nào của sàn chưa rõ, thì sẽ tạo 1 UI để test API đó."*

- Probe là **code của module** (`modules/<id>/ui/dev_probes/<ten>_probe.py`), gọi **đúng adapter/port
  thật** của module đó (không gọi SDK thô — guard *only the session factory constructs binance client*
  vẫn áp dụng), hiển thị request đã gửi + response thô + lỗi đã dịch. Nó là bằng chứng sống cho câu
  "API này hoạt động thế nào" trước khi viết use case.
- Vòng đời probe: **tạm**. Khi API đã rõ và use case đã có test, probe **xoá** hoặc giữ như công cụ
  vận hành — quyết ở PR đó, ghi vào task. Không để probe thành tính năng ngầm.
- Probe đầu tiên (Phase 1, `trading`): "Exchange API tester" — chọn endpoint trong danh sách adapter
  đang bọc (`positionRisk`, `openOrders`, `exchangeInfo` filter cho 1 symbol, `listenKey`), bấm, xem
  payload. Đây là thứ đã thiếu khi điều tra `BUG-117` (phải đọc log thay vì gọi thử).
- Không probe nào nạp khi `dev.mode=false` — surface `dev_board` không tồn tại thì factory không chạy.

## 4.5 Ai sở hữu widget nào (Trading + Dev Board)

| Widget | Module sở hữu | Trading | Dev Board |
| :--- | :--- | :-: | :-: |
| Chart card (1 symbol) / chart list (n symbol) | `charting` (host) + `market_data` (feed) | 1 | n |
| Positions table, Open orders table (+ huỷ 1 lệnh) | `trading` | ✅ | ✅ |
| Manual order card | `trading` | 🔵 (hôm nay chỉ Dev Board — user quyết có đưa lên Trading không; cơ chế cho phép bằng 1 dòng) | ✅ |
| Session card, Enable/Disable, Emergency stop, WS pill | `trading` | ✅ | ✅ |
| Equity chart | `trading` (adapter) + `charting` | ✅ | ✅ |
| Strategy card, last signal card, params dialog | `strategy` | ✅ | ✅ |
| Strategy overlay trên chart | `strategy` | ✅ | 🔵 |
| Indicator script checklist | `indicators` | — | ✅ |
| System controls (market/symbol/date range/load/start/stop), symbol picker | `market_data` | context bar rút gọn | ✅ |
| API probes | mỗi module | — | ✅ |
| Log console | `ui_kit` | ✅ | ✅ |
