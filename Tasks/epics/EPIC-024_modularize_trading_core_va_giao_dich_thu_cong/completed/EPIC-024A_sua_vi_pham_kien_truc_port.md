# EPIC-024A — Sửa vi phạm kiến trúc: handler dùng port thay vì class cụ thể

- **Trạng thái:** ✅ Hoàn thành (2026-09-09)
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

---

## 5. Kết quả xây dựng

**Port mới:** `src/application/ports/i_trading_session_factory.py` — 2 kiểu:

- `ITradingSessionClient` (`typing.Protocol`, không phải `ABC`) — chỉ khai đúng 10 lời gọi
  `futures_*` mà hai bên tiêu thụ `ExchangeSessionFactory.create_trading_client()` thật sự dùng:
  6 lời gọi của `FuturesTradingClient` (`futures_create_test_order`, `futures_create_order`,
  `futures_cancel_order`, `futures_cancel_all_open_orders`, `futures_get_open_orders`,
  `futures_position_information`) + 4 lời gọi của `FuturesAccountReader`
  (`futures_ping`, `futures_time`, `futures_account`, `futures_get_position_mode`) — cả hai đều đi
  qua cùng một `create_trading_client()`, nên Protocol phải phủ cả hai, không chỉ phía application.
  Dùng `Protocol` (structural), không `ABC`, chính là cách port này **không phải import
  `binance.client.Client`** — đúng ràng buộc `IExchangeSessionFactory`'s docstring đã nêu từ đầu.
- `ITradingSessionFactory` (`ABC`) — 1 hàm `create_trading_client(credentials) -> ITradingSessionClient`.

**`ExchangeSessionFactory`** (`src/infrastructure/binance/exchange_session_factory.py`): implement
thêm `ITradingSessionFactory` (bên cạnh `IExchangeSessionFactory` cũ). `create_trading_client()`
đổi kiểu trả về từ `Client` sang `ITradingSessionClient` — object trả về vẫn là `Client(...)` y hệt,
chỉ bọc `cast()` vì `Client` không có type stub (mypy coi là `Any`, trả `Any` cho hàm khai kiểu cụ
thể sẽ bị `no-any-return`). `create_futures_metadata_client()` (không liên quan trading, chỉ dùng
nội bộ infra) giữ nguyên, ngoài phạm vi.

**`FuturesTradingClient`** (`src/infrastructure/binance/futures_trading_client.py`): tham số
constructor `session_factory` đổi kiểu từ `ExchangeSessionFactory` (concrete) sang
`ITradingSessionFactory` (port) — bắt buộc phải đổi cùng lúc với 3 handler, vì đây là nơi 3 handler
truyền factory của chúng vào. Bỏ import `binance.client.Client` (không còn dùng trực tiếp).

**3 handler** (`execute_order`, `enable_trading`, `emergency_stop`): tham số constructor
`session_factory` đổi từ `ExchangeSessionFactory` sang `ITradingSessionFactory`. Vẫn giữ nguyên việc
tự dựng `FuturesTradingClient(...)` bên trong `execute()` — đó là hành vi đã được `EPIC-021G`/
`EPIC-021K` chốt và vẫn đúng phạm vi AST allowlist, không phải thứ EPIC-024A đổi.

**`binance_bot_module.py`:** đăng ký thêm `app.container.singleton(ITradingSessionFactory,
session_factory)` cạnh đăng ký `IExchangeSessionFactory` hiện có — cùng một instance
`session_factory` được chia sẻ cho cả hai port. Trước đây (không có đăng ký này), container tự
dựng một `ExchangeSessionFactory` MỚI mỗi lần resolve tham số kiểu đó cho 3 handler (do
`StdLibContainer._resolve()` auto-construct khi không có gì đăng ký khớp type hint) — vô hại vì
class này không giữ state gì ngoài `market_data_venue`, nhưng vẫn là một instance khác với
`session_factory` biến cục bộ dùng ở những nơi khác trong module này. Sau khi đổi, 3 handler dùng
đúng chung một singleton — tác dụng phụ tích cực, không phải hành vi mới cần test riêng.

**Ngoài phạm vi (giữ nguyên, không đổi):** `FuturesAccountReader`, `FuturesUserDataStream` — cả hai
vẫn nhận `ExchangeSessionFactory` cụ thể (infra gọi infra, không vi phạm §3), không được đăng ký
qua container (được new trực tiếp trong `binance_bot_module.py` với biến `session_factory` cục bộ).

**Sửa kèm không liên quan kiến trúc:** `.agents/Skills/scribe.prompt.md` trỏ tới
`Tasks/epics/EPIC-002.../incomplete/EPIC-002D_....md` — file đã chuyển sang `completed/` từ trước,
khiến cổng "Skill Prompt References" đỏ trước khi làm gì trong epic này. Sửa đường dẫn + câu văn
(EPIC-002D đã đóng, không còn là "sub-task đang mở") vì cổng CI chung không xanh được nếu không sửa,
dù không liên quan tới port/handler.

**Đã chạy:** `pwsh -NoProfile -File scripts/ci-local.ps1 -Full` → `RESULT: PASS`, xác nhận lại bằng
grep trực tiếp log file (`FAILED|ERROR|Traceback|ResourceWarning`) — không có lỗi thật, chỉ có tên
test case chứa chữ "ERROR" (đã PASS). Chạy riêng thêm
`test_order_submission_mode_live_is_restricted.py` + `test_only_the_session_factory_constructs_binance_client.py`
+ `test_task_board_is_consistent.py` — tất cả xanh.
