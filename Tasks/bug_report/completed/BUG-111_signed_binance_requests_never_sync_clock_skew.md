# BUG-111 — Mọi request có ký (`futures_*`) thất bại vĩnh viễn với `-1021` khi đồng hồ máy chạy nhanh — chưa từng đồng bộ `timestamp_offset`

**Reported date:** 2026-09-09
**Severity:** 🔴 P1 — mọi lệnh gọi có ký tới Binance Futures Testnet (đọc vị thế,
đặt lệnh, huỷ lệnh) thất bại **vĩnh viễn**, không phải ngẫu nhiên, một khi đồng
hồ máy chạy nhanh hơn server dù chỉ hơn 1 giây — chặn đứng toàn bộ đường giao
dịch thủ công (`EPIC-024B`) trên máy thật của user.
**Status:** ✅ Đã sửa 2026-09-09 — root-caused, regression-tested, verified.
**Found by:** user chạy app thật trên Testnet (đúng phần "Testnet tier" mà
`EPIC-024B` tự nhận không làm được trong sandbox), gửi log INFO thật.

---

## 1. Symptom

Log thật user gửi trực tiếp trong chat:

```
2026-09-09 19:25:32,652 - App - INFO - Executing query: GetOpenPositionsQuery
2026-09-09 19:25:33,248 - App - ERROR - GetOpenPositionsQuery failed: unknown: APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server's time.
...
2026-09-09 19:25:40,521 - App - INFO - Executing query: GetOpenPositionsQuery
2026-09-09 19:25:40,956 - App - ERROR - GetOpenPositionsQuery failed: unknown: APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server's time.
```

Live Stream (không ký) vẫn chạy bình thường xen giữa hai dòng lỗi — chỉ đường
có ký mới hỏng. Hai lần bấm cách nhau ~8 giây, cả hai đều fail cùng lý do —
không phải flake ngẫu nhiên.

## 2. Root cause

`python-binance`'s `BaseClient._generate_signature()`
(`.venv/.../binance/base_client.py:408`) ký mọi request bằng
`params.setdefault("timestamp", int(time.time() * 1000 + self.timestamp_offset))`,
và `self.timestamp_offset` khởi tạo là `0` (`base_client.py:222`) — nghĩa là
**đồng hồ local dùng thẳng, không hiệu chỉnh**, trừ khi có ai chủ động set
`timestamp_offset`.

`ExchangeSessionFactory.create_trading_client()`
(`src/infrastructure/binance/exchange_session_factory.py`, trước sửa) dựng một
`Client(...)` mới **mỗi lần gọi** (không cache), và không bao giờ chạm tới
`timestamp_offset` — mọi request có ký (`FuturesTradingClient.get_positions/
place_order/cancel_order/get_open_orders`, `FuturesAccountReader.
check_connection`'s `futures_account`/`futures_get_position_mode`) ký bằng
đồng hồ local trần.

Binance từ chối bất kỳ request có ký nào có timestamp **quá 1000ms so với
đồng hồ server** — ngưỡng này **cố định**, `recvWindow` chỉ nới rộng phía "quá
cũ" (bao lâu về trước vẫn còn hợp lệ), không nới được phía "quá mới" (tương
lai). Một máy chạy nhanh hơn server dù chỉ hơn 1 giây khiến **mọi** request có
ký fail vĩnh viễn theo đúng cách này, không phải ngẫu nhiên — khớp đúng log
user gửi (2 lần bấm cách nhau 8s, cả hai đều fail).

Trớ trêu: `FuturesAccountReader.check_connection()` (đã có từ `EPIC-021D`) đã
tự đo đúng độ lệch này qua `client.futures_time()` để hiển thị
`server_time_skew_ms` trên màn "Kiểm tra kết nối" — nhưng chỉ dùng để **hiển
thị**, không bao giờ áp lại vào `timestamp_offset` để sửa. Kể cả nếu có áp,
việc đó cũng chỉ sửa cho đúng 1 client cục bộ của lần gọi đó — mọi lệnh gọi
khác (`GetOpenPositionsQuery`, đặt lệnh, huỷ lệnh, …) đều tự dựng `Client`
riêng mới qua `create_trading_client()`, nên sửa ở một nơi khác không lan
được tới các client khác.

## 3. Fix

Thêm `_sync_timestamp_offset(client)` trong `exchange_session_factory.py`: sau
khi dựng `Client(...)`, gọi `client.futures_time()` (đúng endpoint
`FuturesAccountReader` đã tin dùng để đo skew, không phải endpoint spot chung),
đo `time.time()` ngay trước và ngay sau lệnh gọi, lấy trung điểm làm mốc local
tương ứng, rồi gán:

```python
client.timestamp_offset = server_time_ms - local_at_measurement_ms
```

Đặt đúng **một nơi** — `create_trading_client()`, nơi duy nhất mọi session có
ký được tạo ra (`ADR §2.1` đã ghi rõ điều này) — nên mọi consumer
(`FuturesTradingClient`, `FuturesAccountReader`) tự động được sửa, không cần
sửa từng call site. Chi phí: thêm 1 round-trip HTTP không ký mỗi lần dựng
client — cùng hạng chi phí `Client(...)`'s constructor đã tự trả từ trước
(ping lúc dựng, `BUG-045`), và các client này vốn đã được dựng lại mỗi lần gọi
(không cache) nên không có tần suất cao bất ngờ nào phát sinh thêm.

`create_market_data_client()`/`create_futures_metadata_client()` không đổi —
cả hai không gắn API key, không bao giờ ký request, nên `timestamp_offset`
không có tác dụng ở đó.

## 4. Regression test

`tests/integration/infrastructure/binance/test_exchange_session_factory_against_fake_server.py::
test_create_trading_client_syncs_timestamp_offset_against_the_exchange_clock`
— fake server's `/fapi/v1/time` (`tests/sanity/fake_exchange/futures_routes.py`)
luôn trả `serverTime: 0` (Unix epoch, cách xa đồng hồ thật bất kỳ lúc nào), nên
độ lệch đúng là một số **âm lớn** gần `-(giờ hiện tại tính bằng ms)` — không
phải `0` (giá trị mặc định `python-binance` để lại nếu không sửa).

Xác nhận đỏ đúng lý do trước khi sửa (comment tạm dòng gọi
`_sync_timestamp_offset(client)`, chạy lại):

```
assert -local_after_ms <= client.timestamp_offset <= -local_before_ms
E   assert 0 <= -1788956938242
E    +  where 0 = <binance.client.Client object at 0x...>.timestamp_offset
```

Khôi phục dòng gọi, chạy lại: pass. Không sửa/xoá test nào khác đã có trong
file.

## 5. Xác minh

- `pytest tests/integration/infrastructure/binance/`: 3 passed (2 cũ + 1 mới).
- `pytest tests/integration/infrastructure/binance/ tests/integration/application/test_manual_order_pipeline_against_fake_server.py tests/integration/application/test_live_trading_pipeline_against_fake_server.py tests/unit/infrastructure/binance/`: 163 passed — không lùi bước nào ở các đường dùng chung `ExchangeSessionFactory`/`FuturesTradingClient`.
- `ruff check`/`ruff format --check` trên 2 file đã sửa: sạch.
- `mypy --config-file pyproject.toml src/infrastructure/binance/exchange_session_factory.py`: `Success: no issues found in 1 source file`.
- CI gate đầy đủ (`ci-local.ps1 -Full`) chạy sau khi gộp cùng các thay đổi khác trong phiên; xác nhận bằng grep log file thật.

## 6. Vì sao không bắt được từ trước

`FuturesAccountReader.check_connection()` đã đo đúng con số này từ `EPIC-021D`
(`server_time_skew_ms`), và test của riêng nó
(`tests/unit/infrastructure/binance/test_futures_account_reader.py` — tồn tại
từ trước) đã xác nhận đúng con số đo được hiển thị ra UI — nhưng không có test
nào ở tầng nào từng đặt câu hỏi ngược lại: "con số đo được đó có được *áp
dụng* để sửa request tiếp theo không?". Một chỉ số hiển thị đúng dễ khiến
người đọc yên tâm rằng cơ chế đã hoàn chỉnh, trong khi nó chỉ là phân nửa —
đo mà không sửa. Sandbox này tự khai egress `*.binance.*` bị chặn nên đường
Testnet thật chưa từng chạy được ở đây; bug chỉ lộ ra khi user tự chạy app
thật trên máy có đồng hồ lệch, đúng khoảng trống `EPIC-024B` đã ghi nhận từ
đầu ("Testnet tier — không làm được trong sandbox").
