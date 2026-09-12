# §2 — Context map

## 2.1 Bản đồ

```
                 ┌──────────────────────────── shell/ (Martin's "Main") ────────────────────────────┐
                 │  danh sách module tường minh · surfaces: trading / dev_board / settings · CLI    │
                 └───────────────────────────────────────────────────────────────────────────────────┘
                                                      │ chỉ biết IExtension + contracts/
   ┌──────────────┐    IHistoricalKlines     ┌──────────────┐   IOrderSubmission    ┌──────────────┐
   │ market_data  │ ───────────────────────▶ │  strategy    │ ────────────────────▶ │   trading    │
   │ (Supporting) │    MarketTickEvent       │  (CORE)      │   ITradingSession     │ (Supporting) │
   └──────────────┘                          └──────────────┘   .claim_symbol()     └──────────────┘
          │  IHistoricalKlines                      ▲  IStrategyCatalog                     │
          │  IMarketDataSync · IRangeCoverage       │  IStrategyEngineFactory                │ (không phụ thuộc
          ▼                                         │                                        │  module nghiệp vụ nào)
   ┌──────────────┐ ────────────────────────────────┘
   │ backtesting  │  (Supporting) — ACL: PaperExchange ⇄ StrategyContext
   └──────────────┘

   support/ (Generic):  binance_gateway · charting · indicators · ui_kit      core/: contracts · vo (Published Language)
   kernel (Engine):     DI · bus · config · log · thread · scheduler · hosted · (navigation — Phase 5)
```

Mũi tên = **hướng phụ thuộc** (A → B: A import `modules/B/contracts/`). Không có mũi tên ngược, không
có chu trình — guard `test_module_boundaries.py` (§6) khoá điều này.

## 2.2 Distillation — cái gì là lõi

| Loại | Module | Vì sao |
| :--- | :--- | :--- |
| **Core domain** | `strategy` | Lý do app tồn tại: biến ý tưởng giao dịch thành tín hiệu. Là chỗ user đổi nhiều nhất, sáng tạo nhiều nhất. Mọi module khác tồn tại để **nuôi** (market_data), **thi hành** (trading) hoặc **kiểm chứng** (backtesting) nó |
| **Supporting** | `market_data`, `trading`, `backtesting` | Cần thiết, có nghiệp vụ riêng, nhưng thay được bằng cách khác (sàn khác, mô phỏng khác) mà app vẫn là app này |
| **Generic** | `support/{binance_gateway, charting, indicators, ui_kit}` | Kỹ thuật thuần; về lý thuyết mua/tải được từ ngoài |

Hệ quả thực dụng: **đầu tư chất lượng** (test, review, thời gian thiết kế) ưu tiên `strategy` →
`trading` → còn lại. Và: `strategy` **không được** phụ thuộc chi tiết của sàn — nó chỉ thấy
`trading.contracts` và `market_data.contracts`.

## 2.3 Kiểu tích hợp giữa từng cặp (DDD context-map patterns)

| Cặp (upstream → downstream) | Pattern | Cụ thể |
| :--- | :--- | :--- |
| `market_data` → `strategy`, `trading`, `backtesting` | **Open Host Service + Published Language** | `IHistoricalKlines`, `IMarketStream`, `IMarketDataSync`, `IRangeCoverage`; ngôn ngữ chung = `core/vo` (`MarketData`, `TimeFrame`) và `MarketTickEvent` |
| `trading` → `strategy` | **Customer/Supplier** — `trading` là supplier, `strategy` là customer | `IOrderSubmission`, `ITradingSession`, `IAccountSnapshot`. `trading` **không biết** `strategy` tồn tại |
| `strategy` → `backtesting` | **Customer/Supplier** — `strategy` supplier | `IStrategyCatalog`, `IStrategyEngineFactory`. `backtesting` **chạy** chiến lược; chiến lược không biết mình đang được backtest |
| `backtesting` ⇄ `PaperExchange` vs `StrategyContext` | **Anticorruption Layer** trong `backtesting` | Hôm nay `domain/strategies/strategy_context.py` + 3 strategy import type của `domain/backtesting` (ST → BT, **sai chiều**). To-be: `strategy` định nghĩa `StrategyContext` của nó (candle, vị thế hiện tại dưới dạng VO trung tính); `backtesting/adapters/` dịch `PaperExchange` → `StrategyContext`. `trading` cũng cung cấp `StrategyContext` từ `LivePosition` |
| `support/binance_gateway` → `market_data`, `trading` | **Anticorruption Layer** dùng chung cho SDK | Chỉ gateway được dựng `binance.client.Client` (guard test đã có). Mỗi context bọc phần SDK **của nó** trong `adapters/` riêng: `market_data/adapters/binance/` (REST klines, market WS), `trading/adapters/binance/` (futures REST, user-data WS) |
| `support/charting` ← mọi module có chart | **Conformist** (downstream chấp nhận model của upstream) | Module vẽ bằng `IChartHost` + `MarkerPoint`/`RegionSpan`/`InfoField` của charting — không dịch |

## 2.4 Published Language — `core/vo`

**Không gọi là "Shared Kernel"** (`architecture-rule.md` đã định nghĩa Shared Kernel = đúng 2 symbol
Engine `IDomainEvent`, `BaseEvent`, có test khoá). `core/vo` là **Published Language**: value object
trung tính về ngôn ngữ nghiệp vụ, immutable, mọi module đọc, **không module nào sở hữu**.

**Luật vào:** đã có ≥2 consumer ở ≥2 module khác nhau (đo, không đoán). Guard: `core/` không import
`modules/*`, `support/*`, PySide6.

| VO | Consumer đo được (2026-09-11) | Vào `core/vo`? |
| :--- | :--- | :-: |
| `TimeFrame` | cả 4 tầng, 5 package | ✅ |
| `OrderSide`, `PositionSide` | application, domain, infrastructure, presentation | ✅ |
| `MarketDataVenue`, `TradingVenue` | mọi tầng + composition root | ✅ |
| `Currency`, `MarketType` | domain + presentation | ✅ |
| `MarketData` (candle OHLCV, `domain/entities/market_data.py`) | MD, BT, ST, IND, CH | ✅ — đổi tên `Candle` là **ứng viên**, làm sau (rename storm, không phải refactor thuần) |
| `PositionSizing`, `PositionSizingType` | BT, TR (`position_sizing_bridge`), ST | ✅ |
| `ExchangeCredentials`, `VenueAlignment` | kernel + settings | ✅ (`core/vo` hoặc `support/binance_gateway/contracts`) |
| `SignalAction`, `Signal`, `LiveStrategyConfig` | chỉ ST (+TR qua bridge) | ❌ → `strategy/contracts` |
| `BrokerSimulationConfig`, `CommissionType` | chỉ BT | ❌ → `backtesting/domain` |
| `ExchangeConnectionStatus`, `PositionMode`, `MarginType` | TR + settings | ❌ → `trading/contracts` (settings section là của trading góp) |
| `Symbol` | **không tồn tại** — symbol là `str` thô khắp nơi | ❌ không phát minh trong epic này; ghi nhận ứng viên |

## 2.5 Sự kiện vượt ranh giới (đo publisher/subscriber thật)

Chỉ event **trong `contracts/`** mới tồn tại với bên ngoài. Bảng này là danh sách **đầy đủ** event
cross-module sau khi cắt; event nào không có ở đây là internal của module.

| Event | Publisher (module) | Subscriber ngoài module | Ghi chú |
| :--- | :--- | :--- | :--- |
| `MarketTickEvent` | `market_data` (market WS) | `strategy` (tick → engine), `trading` (chart live), surfaces | ✅ đã là bus event |
| `SingleSyncProgressEvent` | `market_data` | `backtesting` (data_sync), surfaces | ✅ |
| `SignalGeneratedEvent` | `strategy` | `backtesting` (log/marker), surfaces (card "last signal") | ✅ — `LiveTradingCoordinator` tiêu thụ **trong tiến trình** (không qua bus): giữ, là internal của `strategy` |
| `LiveOrderBlockedEvent` | `strategy` (`LiveTradingCoordinator` — dời về strategy vì nó là "quyết định không gửi lệnh") | surfaces | ⚠️ hôm nay ở `application/services/` không chủ |
| `OrderFilledEvent`, `PositionChangedEvent`, `PositionClosedEvent`, `EquitySampledEvent` | `trading` | `charting` (fill marker qua adapter của trading), surfaces | ✅ |
| `TradingSessionChangedEvent` 🔵 | `trading` | surfaces (thay cho 3 Presenter đọc thẳng `TradingSessionState`) | mới — thay đổi **cơ chế**, không đổi nghiệp vụ |
| `StrategyArmedEvent` / `StrategyDisarmedEvent` 🔵 | `strategy` | surfaces | mới — thay cho `LiveStrategySession` bị 2 Presenter đọc thẳng |
| `BacktestCompletedEvent`, `BacktestFailedEvent` | `backtesting` | — | **internal** (chỉ screen backtest nghe) |
| `OrderSubmittedEvent`, `OrderRejectedEvent` | **không ai** | **không ai** | chết — xoá ở Phase 1 |
| `BulkSyncProgressEvent` | `market_data` | — | internal |

Mỗi event cross-module có **đúng một Feed** normalizing ở module sở hữu (`architecture-rule.md` §6),
surface chỉ *hiển thị* qua widget module góp.
