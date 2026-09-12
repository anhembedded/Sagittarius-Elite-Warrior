# EPIC-025D — Phase 3: `modules/backtesting`

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** C · **Chặn:** E
- **Đọc trước:** HLD §3.5; ADR D12. Đây là phần **lớn nhất về dòng code** (screen backtest 12.309
  dòng / 60 file) nhưng **ít dây nhất**: chỉ phụ thuộc `market_data.contracts` + `strategy.contracts`.

## 1. Việc cần làm

1. `modules/backtesting/`: `domain/backtesting` (PaperExchange, `_OpenPosition` — **không** gộp với
   `LivePosition`, HLD §1 C3), `use_cases/backtest`, screen backtest.
2. Sửa vi phạm §3 sẵn có: `backtest_presenter.py:43` import `infrastructure/persistence` → qua
   `market_data.contracts`.
3. `contracts/`: `IBacktestRunner` (cho CLI), DTO kết quả; chart overlay fill/marker góp qua
   `chart_overlay`.

## 2. Xong khi

- Backtest chạy end-to-end với kết quả **bit-identical** trên cùng dữ liệu (so sánh trade log
  trước/sau — refactor thuần).
