# §3 — Hợp đồng module

## 3.1 `BoundedContextModule` — đứng trên `IExtension` của Engine ✅/🔵

Engine đã có (đo 2026-09-11, `sagittarius_engine/interfaces/i_extension.py`): `IExtension[TContext]`
với đúng 3 abstract `register` / `boot` / `shutdown`; `descriptor` mặc định đọc **class attribute**
`dependencies`, `optional_dependencies`, `priority`, `enabled`; `ExtensionManager` topo-sort theo
`dependencies`, `ExtensionDependencyError` khi thiếu, `ExtensionCircularDependencyError` khi có chu
trình, rollback khi `register()` ném. **Không tạo `IModule` mới** (ADR D2).

```python
# src/core/contracts/bounded_context_module.py  🔵
class BoundedContextModule(IExtension[IEngineContext], ABC):
    """Một bounded context = một IExtension + 2 hook UI.

    `module_id` là PUBLIC CONTRACT: nằm trong route, ui_state persist, tên event, owner id của
    stream/action. Đổi = breaking change, phải migrate state.
    """
    module_id: ClassVar[str]                      # "market_data" — trùng `IExtension.name`
    dependencies: ClassVar[list[str]] = []        # CHỈ module_id mà mình dùng contracts/ (Engine topo-sort)

    # --- Engine đã có ---
    @abstractmethod
    def register(self, context: IEngineContext) -> None: ...
        # CHỈ khai báo DI (singleton/bind). CẤM resolve(), CẤM I/O, CẤM Qt.
    @abstractmethod
    def boot(self, context: IEngineContext) -> None: ...
        # Mọi module đã register → được resolve; start hosted service, scheduler job.
    def shutdown(self, context: IEngineContext) -> None: ...

    # --- app thêm (policy, không phải mechanism Engine) ---
    def contribute(self, registry: IContributionRegistry) -> None: ...   # §4
    def subscribe(self, bridge: QtEventBridge) -> None: ...              # subscription UI của riêng module
```

**Ba luật** (có guard/test):

1. `register()` không `resolve()` — thứ tự nạp không đổi kết quả. Test: `register()` chạy với một
   container spy; bất kỳ `resolve` nào → fail.
2. `dependencies` chỉ được chứa `module_id` mà module thật sự import `contracts/` của họ — guard so
   sánh danh sách khai báo với import AST thật (thừa cũng fail, thiếu cũng fail).
3. Module **construct được không có Qt** — `domain/` + `application/` không import PySide6 (guard).

⚠️ Đã đo: `StdLibContainer.singleton()/bind()` **ghi đè im lặng**, không có `try_bind`/`has`; chỉ
có `registrations()`. → `shell/` sau vòng `register()` kiểm tra không có abstract nào được 2 module
cùng claim (dùng `registrations()`), fail-fast trước `boot()`.

⚠️ Đã đo: `ExtensionManager.register()` **initialize ngay** các extension đã đủ dependency, và coi
`optional_dependencies` như bắt buộc ở bước này. → Không dùng `optional_dependencies`; `shell/`
gọi `app.use()` theo **thứ tự topo của chính nó** (danh sách tường minh đã sắp sẵn) để không phụ
thuộc hành vi này.

## 3.2 Bố cục bên trong một module — Clean Architecture, directory = layer

```
src/modules/<module_id>/
├── module.py            # BoundedContextModule subclass — nơi DUY NHẤT của module import cả 4 tầng
├── contracts/           # PUBLIC — bề mặt duy nhất người ngoài được import
│   ├── i_*.py           #   port: ABC đặt tên I* (architecture-rule §2.1), 1 file / 1 ABC
│   ├── dto/             #   frozen dataclass phẳng — không entity, không method nghiệp vụ
│   └── events/          #   BaseEvent subclass — chỉ event cross-module (§2.5)
├── domain/              # entity, VO riêng, policy — import: core/vo, Shared Kernel (2 symbol). KHÔNG PySide6
├── application/         # use case (command/query handler), service, feed-normalizer — import: domain, contracts (mình + người khác), core
├── adapters/            # implement port: exchange, persistence, engine_adapters — import: application, support/*
└── ui/                  # presentation: presenter, view model, coordinator, Python wrapper widget, dev_probes/
    └── dev_probes/      #   widget probe API (§4.3) — chỉ nạp khi dev.mode
```

Luật phụ thuộc **trong** module (guard sẵn có `architecture-rule` §3, tổng quát hoá theo đường dẫn
`modules/*/{domain,application,adapters,ui}` ở Phase 0): `ui → application → domain`; `adapters →
application`; `ui` **không** import `adapters` (2 vi phạm hôm nay: `backtest_presenter.py:43`,
`settings_presenter.py:21` — sửa khi module đó di trú).

**QML**: file `.qml` **vẫn** ở `src/presentation/ui/qml/<Widget>/` (ADR D6); Python wrapper (`*Panel`,
`*VM`) của widget đặc thù module chuyển về `modules/<id>/ui/widgets/`. Wrapper dùng chung (DataTable
skeleton, kit) ở `support/ui_kit`.

**CLI**: mỗi module sở hữu lệnh CLI của nó (`modules/<id>/ui/cli/`), góp qua contribution `cli_command`
(§4); `shell/` dựng parser. `trade-once` (chạm MD+ST+TR) thuộc `strategy` — nó là "chạy chiến lược một
lần", dùng `contracts` của hai module kia.

**Test**: theo tier (ADR D7): `tests/unit/modules/<id>/…`, `tests/integration/modules/<id>/…`; guard kiến
trúc ở `tests/unit/architecture/`.

## 3.3 Bốn loại vật trong `contracts/` — và loại nào KHÔNG được có

| Loại | Là gì | Ví dụ | Ai gọi |
| :--- | :--- | :--- | :--- |
| **Port** (ABC `I*`) | request/response đồng bộ, typed; module sở hữu implement trong `application/` và đăng ký DI ở `register()` | `IHistoricalKlines.load(symbol, timeframe, start, end) -> tuple[MarketData, ...]` | module khác `resolve(IHistoricalKlines)` |
| **DTO** | snapshot phẳng, frozen; **không** là entity | `PositionSnapshot`, `RangeCoverageSnapshot` | trả về từ port; payload event |
| **Event** | `BaseEvent`, fire-and-forget, nhiều người nghe | `OrderFilledEvent` | bus (`IEventPublisher`), nghe qua `QtEventBridge` |
| **Widget factory** (chỉ qua §4 contribution, không nằm trong `contracts/`) | `Callable[[IContainer], QWidget]` | positions table | surface |

**Không được có trong `contracts/`:** entity/aggregate, Command/Query class của use case nội bộ,
Coordinator, bất kỳ thứ gì import `adapters/` hay PySide6 (trừ type `QWidget` trong widget factory).

**Vì sao port ABC, không phải "dispatch Query class của module khác"** (quyết theo doctrine —
pattern có tên: *module public API interface* của modular monolith; `architecture-rule` §2.1):
(a) typed — hết `cast(object)` trên `ICommandDispatcher.dispatch()`; (b) `resolve(IPort)` thiếu
supplier → fail-fast ở boot nhờ `dependencies` + DI, thay vì lỗi runtime; (c) Command/Query class
của module là **internal** — đổi thoải mái không vỡ ai. Bên trong module, UI của nó vẫn dispatch
Command/Query của nó qua `ICommandDispatcher` như hôm nay.

## 3.4 Contracts từng module — vòng 1

Nguyên tắc chọn: **có consumer ở module khác** (đo bảng call-site 2026-09-11) → public; không → internal,
dù hôm nay đang là port ở `application/ports/`. Danh sách này là **tối thiểu cần cho di trú**;
thêm port = thêm consumer thật, ghi vào HLD trong cùng PR.

### `market_data` (Supporting — Open Host Service)

| Contract | Kiểu | Consumer đo được | Từ code hôm nay |
| :--- | :--- | :--- | :--- |
| `IHistoricalKlines` | port | backtesting (2 coordinator), trading (chart), dev_board, CLI `trade-once` | `GetHistoricalKlinesQuery` |
| `ISymbolCatalog` | port | backtesting, dev_board picker, trading combo | `ListAvailableSymbolsQuery`, `ISymbolCatalogRepository` |
| `IMarketDataSync` | port | trading (`chart_coordinator.py:145`), backtesting (`data_sync_coordinator.py:217`), dev_board | `SyncMarketDataCommand` |
| `IMarketStream` | port | trading (`chart_coordinator.py:191`), dev_board, CLI `stream` | `StartLiveStreamCommand`/`Stop…`, `ILiveStreamService`, owner id |
| `IRangeCoverage` | port | backtesting | `GetBacktestRangeCoverageQuery` (đổi tên: coverage là khái niệm của market_data, backtest chỉ là caller đầu tiên) |
| `MarketTickEvent`, `SingleSyncProgressEvent` | event | strategy, trading, backtesting | đã có |
| `RangeCoverageSnapshot`, `SyncProgress` | DTO | — | `application/ports/i_market_data_repository.py` (tách DTO ra khỏi file port) |
| **Internal** | | | `IMarketDataRepository`, `IExchangeClient`, bulk sync, clear/prune/repair/audit/scan, gap, kline inspector, `InFlightSyncGuard`, `ISymbolMarketMetadataCache` (⚠️ chưa từng được đăng ký DI — `backtest_presenter.py:386` âm thầm tự dựng; dọn ở Phase 3) |

### `trading` (Supporting — Supplier của `strategy`)

| Contract | Kiểu | Consumer đo được | Từ code hôm nay |
| :--- | :--- | :--- | :--- |
| `IOrderSubmission` | port | strategy (`LiveTradingCoordinator`), CLI `trade-once`/`order-dry-run` | `PreviewOrderQuery` + `ExecuteOrderCommand` + `CancelOrderCommand` — **đường duy nhất** gửi lệnh (chứng minh bởi `EPIC-024B`) |
| `ITradingSession` | port | strategy (`claim_symbol` — xem dưới), surfaces | `EnableTrading`/`DisableTrading`/`EmergencyStop` + snapshot của `TradingSessionState` |
| `IAccountSnapshot` | port | strategy (`live_strategy_factory`, `arm_strategy` — kiểm tra số dư) | `ITradingAccountReader` |
| `OrderFilledEvent`, `PositionChangedEvent`, `PositionClosedEvent`, `EquitySampledEvent`, `TradingSessionChangedEvent` 🔵 | event | charting adapter, surfaces | đã có (trừ event mới) |
| `OrderIntent`, `OrderPreview`, `PositionSnapshot`, `OpenOrderSnapshot`, `TradingSessionSnapshot`, `AccountSnapshot` | DTO | — | `LivePosition` **không** ra ngoài; `PositionSnapshot` là DTO phẳng của nó |
| **Internal** | | | `ITradingClient`, `IUserDataStream`, `ITradingSessionFactory`, `IMarketMetadataProvider` (order shaping), `IFuturesSymbolMetadataCache`, `TradingLimitPolicy`, `PositionRefreshService`, `EquityCurveRecorder`, `GetExchangeConnectionStatusQuery` (settings section + CLI `exchange-status` đều là **của trading**) |

**Worked example — chiều phụ thuộc giải một chu trình.** `EPIC-024B` §4.1.2: lệnh tay bị chặn cứng khi
chiến lược đang arm **cùng symbol**. Nếu `trading` hỏi `strategy` "đang arm gì?" → `trading → strategy`,
mà `strategy → trading` (gửi lệnh) → **chu trình**. Giải bằng khái niệm **của trading**: *symbol lease*.
`ITradingSession.claim_symbol(symbol, owner_id) / release_symbol(symbol, owner_id)`; `trading` từ chối
lệnh tay trên symbol đã bị claim mà **không biết ai claim**; `strategy` claim khi arm, release khi
disarm. Cùng hình với `ActionOwnershipTracker` đã có. Tổng quát: caller tự động thứ hai (bot khác,
copy-trade) dùng đúng cơ chế, không sửa `trading`.

### `strategy` (CORE — Supplier của `backtesting`, Customer của `trading` + `market_data`)

| Contract | Kiểu | Consumer đo được | Từ code hôm nay |
| :--- | :--- | :--- | :--- |
| `IStrategyCatalog` | port | backtesting (picker, params form), surfaces (card) | `StrategyRegistry` |
| `IStrategyEngineFactory` | port | backtesting (`run_static`, `run_historical_tick`) | `StrategyEngine` + `strategy_factory` |
| `StrategyContext` | DTO/ABC (input cho chiến lược: candle buffer + vị thế hiện tại **trung tính**) | backtesting (ACL từ `PaperExchange`), trading (từ `LivePosition`) | `domain/strategies/strategy_context.py` — hôm nay import `domain/backtesting` (**sai chiều**, sửa Phase 2/3) |
| `SignalGeneratedEvent`, `StrategyArmedEvent` 🔵, `StrategyDisarmedEvent` 🔵, `LiveOrderBlockedEvent` | event | backtesting, surfaces | đã có / mới |
| `StrategyDescriptor`, `ArmedStrategySnapshot`, `Signal`, `SignalAction` | DTO | — | `value_objects/{signal,signal_action}.py` |
| **Internal** | | | `LiveStrategySession`, `LiveStrategyFactory`, `LiveStrategyConfigStore`, `LiveTradingCoordinator` (tick → signal → `IOrderSubmission`), `MarketTickEventHandler` (dời từ `event_handlers/market_data/` — nó lái strategy, không phải market_data), `StrategyArmingCoordinator`, `arm/disarm` use case (dời từ `use_cases/trading/`), `IndicatorScriptRegistry` consumer |

### `backtesting` (Supporting — Customer của `market_data` + `strategy`)

| Contract | Kiểu | Consumer | Ghi chú |
| :--- | :--- | :--- | :--- |
| *(chưa có port public)* | — | không module nào cần | `RunBacktestCommand`/`StopBacktestCommand`/`BacktestState` bound nhưng **không ai dispatch** → xoá Phase 3; nếu CLI `backtest` xuất hiện thì thêm `IBacktestRunner` lúc đó |
| `BacktestCompletedEvent`, `BacktestFailedEvent` | event **internal** | screen của chính nó | không vào `contracts/` |
| **Internal** | | | `PaperExchange`, `_OpenPosition`, `Trade`, metrics, `out_of_sample_*` (⚠️ `out_of_sample_split.py` import `IMarketDataRepository` — domain → port, sửa: dùng `IHistoricalKlines` từ application), `BrokerSimulationConfig`, fee/margin/matching policy, 11 modal, 9 coordinator |

### `support/*` (Generic)

| Package | Contracts | Consumer |
| :--- | :--- | :--- |
| `binance_gateway` | `IExchangeSessionFactory` (market), `ITradingSessionFactory` (trading), `IExchangeCredentialsProvider`, `binance_endpoints` (venue → base URL/testnet), `BinanceErrorTranslator` | `market_data/adapters`, `trading/adapters`, settings section |
| `charting` | `IChartHost` (tổng quát hoá `IBacktestChartHost` đã có ở `screens/backtest/logic/backtest_chart_host.py`), `MarkerPoint`, `RegionSpan`, `InfoField`; `ChartCard` (QtWidgets vĩnh viễn) | trading, strategy overlay, backtesting, indicators runner |
| `indicators` | `IIndicatorCatalog` (script list + runner), `IIndicator` | strategy (toán), backtesting, dev_board checklist |
| `ui_kit` | không port; widget + token + `ActionOwnershipTracker`, `BaseFeed`, `app_defaults`, `sync_progress_*` | mọi module |

### `core/` (app-side kernel policy)

`core/contracts/`: `BoundedContextModule`, `IContributionRegistry` + descriptor (§4), `ICommandDispatcher`,
`IEventPublisher`, `IConfigReader` (3 port engine-adapter hôm nay ở `application/ports/`).
`core/vo/`: bảng §2.4. **Không** có nghiệp vụ, không PySide6.

## 3.5 Bảng ánh xạ code hôm nay → module (rút gọn; đầy đủ trong từng task `EPIC-025A–E`)

| Hôm nay | Đích | Phase |
| :--- | :--- | :-: |
| `use_cases/{sync,database}`, `queries/{get_database_*, scan_all_databases, audit_database_integrity, get_historical_klines, list_available_symbols, get_backtest_range_coverage}`, `use_cases/stream/*`, `infrastructure/persistence/*` (trừ futures cache), `infrastructure/binance/{client,binance_websocket_service,market_metadata_parser}.py`, `engine_adapters/live_stream_adapter.py`, `screens/data_management`, CLI `sync`/`stream` | `modules/market_data` | 0 |
| `domain/trading`, `use_cases/trading/{enable,disable,emergency_stop,execute_order,cancel_order}`, `commands/submit_order`, `queries/{preview_order,get_open_positions,get_exchange_connection_status}`, `services/{trading_session_state,position_refresh_service,equity_curve_recorder}`, `infrastructure/binance/futures_*`, `user_data_event_parser`, `order_enum_parsing`, `persistence/futures_symbol_metadata_cache`, `entities/futures_symbol_metadata`, `policies/order_quantity_rounding_policy`, `ui/common/{order_feed,equity_feed,equity_chart_adapter,order_fill_marker,market_tick_feed,live_order_book_coordinator,execute_order_block_reason}`, `qml/{PositionsTable,OpenOrdersTable}` wrapper, manual order card, session card, context bar, CLI `exchange-status`/`order-preview`/`order-dry-run` | `modules/trading` | 1 |
| `domain/strategies`, `services/{strategy_engine,strategy_registry,live_strategy_*,live_trading_coordinator}`, `use_cases/trading/{arm,disarm}_strategy`, `event_handlers/market_data/market_tick_event_handler`, `ui/common/{strategy_arming_coordinator,signal_feed,strategy_display}`, strategy card, last-signal card, `StrategyParamsDialog`, `StrategyOverlayCoordinator`, CLI `trade-once` | `modules/strategy` | 2 |
| `domain/backtesting`, `use_cases/backtest`, `services/backtest_range_coverage` (phần tính coverage → market_data), `screens/backtest` (60 file), `ui/common/base_event_logger` | `modules/backtesting` | 3 |
| `infrastructure/binance/{exchange_session_factory,binance_endpoints,binance_error_translator}`, `infrastructure/credentials` | `support/binance_gateway` | 0 (cần cho market_data) |
| `components/chart_card` (27 file), `screens/backtest/logic/backtest_chart_host` (port) | `support/charting` | 4 (port `IChartHost` tách ra ở Phase 1 vì trading cần) |
| `domain/{indicators,indicator_scripts,scripting}`, `services/indicator_script_registry`, `components/indicator_scripts`, `components/strategy_params` | `support/indicators` | 4 |
| `kit/`, `qml/kit`, `qml/DataTable`, `components/{sidebar,environment_banner,market_picker}`, `ui/common/{action_ownership_tracker,app_defaults,base_feed,sync_progress_*,health_*}` | `support/ui_kit` | 4 |
| `value_objects/*` theo §2.4; `application/ports/{i_command_dispatcher,i_event_publisher,i_config_reader}` | `core/` | 0 |
| `binance_bot_module.py`, `main.py::create_app`, `app_bootstrapper.py` tuple 5 module, `cli_parser`, `interactive_shell` | `shell/` | 0 → teo dần, xoá ở 4 |
| **Chết — xoá** (đo 0 reference): `services/{rate_limiter,strategy_factory,position_state_reconciler}`, `events/{OrderSubmitted,OrderRejected}`, `RunBacktestCommand`+`BacktestState`+`StopBacktestCommand`, `qml/StatGrid`, `ui/common/{system_error_feed,system_error_report}` | — | phase của module chứa nó |
