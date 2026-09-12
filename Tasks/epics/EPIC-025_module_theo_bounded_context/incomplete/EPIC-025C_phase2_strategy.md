# EPIC-025C — Phase 2: `modules/strategy` (Core domain)

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** B · **Chặn:** D
- **Đọc trước:** HLD §3.4; ADR D1 (strategy = Core, tách khỏi trading — giá của gộp là `BUG-112`).

## 1. Việc cần làm

1. `modules/strategy/`: `domain/strategies`, `services/live_strategy_*`, `use_cases/trading/{arm,
   disarm}_strategy` (dời khỏi trading), `StrategyArmingCoordinator` (392 dòng, từ `ui/common`),
   `signal_feed`.
2. `contracts/`: `IStrategyCatalog`, `IStrategyEngineFactory` (cho `backtesting` dùng ở Phase 3),
   DTO `StrategyDescriptor`, `ArmedStrategySnapshot`, event `SignalEmitted`, `StrategyArmed`/`Disarmed`.
3. `strategy` **tiêu thụ** `trading.contracts.IOrderSubmission` — không ngược lại (Customer/Supplier:
   `trading` là supplier). Chart overlay tín hiệu góp qua `chart_overlay` (HLD §4).
4. Widget góp: card Chiến lược (Trading + Dev Board dùng chung một bản).

## 2. Xong khi

- Guard: `modules/trading` **không** import gì từ `modules/strategy` (kể cả `contracts/`).
- Arm/disarm + tick → lệnh tự động chạy y như trước trên Testnet (user xác nhận).
