# EPIC-024A — Sửa vi phạm kiến trúc: handler dùng port thay vì class cụ thể

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** — · **Chặn:** — (độc lập hoàn toàn với B/C, có thể làm bất kỳ lúc nào)

## 1. Việc cần làm

3 handler sau import thẳng class cụ thể của Binance thay vì port tương ứng — vi phạm
`.agents/rules/architecture-rule.md` §3 ("không để Infrastructure rò vào Application"), đã xác nhận
ở `PRO-003` §2:

| File | Đang import class cụ thể | Phải đổi sang port |
| :--- | :--- | :--- |
| `src/application/use_cases/trading/execute_order/handler.py` | `FuturesTradingClient`, `ExchangeSessionFactory` | `ITradingClient`, `IExchangeSessionFactory` (hoặc port factory mới nếu §2 dưới đây cần) |
| `src/application/use_cases/trading/enable_trading/handler.py` | như trên | như trên |
| `src/application/use_cases/trading/emergency_stop/handler.py` | như trên | như trên |

## 2. Vấn đề cần xử lý trước khi đổi thẳng

`ExchangeSessionFactory` (concrete) có 2 hàm KHÔNG thuộc port nào (`create_trading_client()`,
`create_futures_metadata_client()`) — trả thẳng `binance.client.Client` thô. 3 handler này cần
CHÍNH XÁC những hàm đó (chúng là 3 nơi duy nhất được phép dựng `FuturesTradingClient` ở chế độ
`LIVE` — có test AST-based enforce điều này, xem `PRO-003` §2). Vì vậy không thể chỉ đổi type hint
sang `IExchangeSessionFactory`/`ITradingClient` hiện có — 2 hàm đó cần một port MỚI (ví dụ
`ITradingSessionFactory` hoặc mở rộng `IExchangeSessionFactory`) trước, rồi mới đổi 3 handler.

## 3. Quyết định thiết kế

- **Không đổi hành vi.** Đây là sửa kiến trúc thuần — cùng object được tạo ra, chỉ khác type hint/
  contract mà application layer nhìn thấy.
- **Không đổi test AST allowlist** (nơi nào được phép dựng `FuturesTradingClient(..., LIVE)`) — vẫn
  đúng 3 file đó, chỉ đổi cách chúng lấy factory.

## 4. Kiểm thử

- Test AST allowlist hiện có phải vẫn xanh (chứng minh không mở thêm chỗ được phép dựng client LIVE).
- `mypy` xanh là bằng chứng đủ cho việc port mới khớp đúng những gì 3 handler cần — không cần test
  hành vi mới vì hành vi không đổi.
- Toàn bộ cổng: `ruff check`/`ruff format --check`/`mypy`/`pytest tests/unit/ tests/integration/
  tests/sanity/` xanh trước khi merge.
