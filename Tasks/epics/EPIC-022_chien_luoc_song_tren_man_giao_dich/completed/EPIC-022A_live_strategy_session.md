# EPIC-022A — `LiveStrategySession`: chiến lược đổi được lúc chạy

**Status:** ✅ Hoàn thành (2026-09-07) · **Chặn bởi:** — · **Repo:** Elite

---

## 1. Vấn đề

`MarketTickEventHandler.__init__(live_symbol, live_interval, strategy_engine,
live_trading_coordinator)` nhận 4 field **chỉ trong constructor**, và `binance_bot_module.py:596-599`
dựng nó đúng một lần rồi `app.event_bus.on(MarketTickEvent, handler.handle)`. Sau thời điểm đó
không có đường nào đổi chiến lược nữa — UI có làm ra combobox cũng không nối vào đâu được.

`LiveTradingCoordinator` cũng đóng băng `live_symbol`/`sizing_percent`/`leverage` lúc dựng
(`live_trading_coordinator.py:86-112`), nên "đổi chiến lược" thực chất phải dựng lại **cả hai**.

## 2. Thiết kế

Tách làm 3 mảnh, mỗi mảnh 1 file (`architecture-rule.md` §5):

| File mới | Vai trò |
| :--- | :--- |
| `src/domain/value_objects/live_strategy_config.py` | `LiveStrategyConfig` — frozen dataclass thuần dữ liệu: `strategy_key`, `strategy_params`, `symbol`, `interval`, `sizing_percent`, `leverage`. Không giữ object sống. |
| `src/application/services/live_strategy_factory.py` | `LiveStrategyFactory.build(config) -> (StrategyEngine, LiveTradingCoordinator)` — gom đúng chỗ hiện đang nằm inline trong `boot()`. |
| `src/application/services/live_strategy_session.py` | `LiveStrategySession` — giữ arming hiện tại, đổi được lúc chạy, khoá bằng `threading.RLock` giống `TradingSessionState` (`BUG-088`). |

**Vì sao snapshot-rồi-thả-khoá, không giữ khoá suốt tick.** `LiveTradingCoordinator.handle()` gọi
mạng thật (`get_or_fetch`, `check_connection`, `dispatch`). Giữ `RLock` suốt quãng đó nghĩa là một
lần `arm()` từ UI thread sẽ **treo UI** vài giây theo đúng độ trễ REST của Binance. Nên
`dispatch_tick()` lấy snapshot `(config, engine, coordinator)` **trong** khoá rồi xử lý **ngoài**
khoá. Hệ quả trung thực: một tick đang bay sẽ chạy nốt bằng engine cũ — chấp nhận được, vì §4.1
của epic đã cấm `arm()` khi giao dịch đang bật, nên cửa sổ này chỉ tồn tại lúc trading đang TẮT
(không có lệnh nào được gửi).

`MarketTickEventHandler` giữ nguyên vai trò adapter event-bus, mất 4 field, nhận 1
`LiveStrategySession`; toàn bộ luật lọc symbol/interval + `on_tick` + `coordinator.handle` chuyển
vào `session.dispatch_tick(md)` để config và engine không bao giờ lệch nhau giữa 2 lần đọc.

## 3. Đổi theo file

- **Mới:** 3 file ở bảng trên.
- `market_tick_event_handler.py` — ctor nhận `session`, `handle()` gọi `session.dispatch_tick`.
- `binance_bot_module.py` — `boot()` dựng `LiveStrategyFactory` + `LiveStrategySession` (DI
  singleton), tự `arm()` từ config **nếu** 3 key `symbol`/`strategy_key`/`interval` đều có
  (giữ nguyên hành vi cũ cho ai đang cấu hình bằng file), và **truyền `params`** — chỗ
  `build_engine` vốn nhận `params` nhưng boot chưa từng truyền.

## 4. Test

`tests/unit/application/services/test_live_strategy_session.py` — arm đổi engine (indicator state
mới), disarm về trơ, `dispatch_tick` lọc đúng symbol/interval, không giữ khoá khi coordinator chạy
(dùng coordinator giả gọi ngược `arm()` để chứng minh không deadlock).
`tests/unit/application/event_handlers/` — handler trơ khi chưa arm.
