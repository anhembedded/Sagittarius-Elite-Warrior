# EPIC-002D — Lộ trình siết `--strict` dần theo module

**Thuộc Epic:** [`EPIC-002`](../README.md)
**Trạng thái:** 🟡 Đang làm — `src/domain/` và `src/application/` (mỗi bên trừ 1-4 file nợ thật đã
biết) đã bật `--strict` thật (2026-09-08, xem §5/§6). Vẫn là backlog dài hạn theo đúng §3 — không
có mốc "xong hẳn", mở rộng dần theo module.
**Phụ thuộc:** [`EPIC-002B`](../completed/EPIC-002B_wire_mypy_into_ci_local.md).

---

## 1. Mục tiêu

`EPIC-002B` chỉ bật `mypy` ở mức tối thiểu (đủ bắt lớp lỗi `BUG-026`). Task
này là nơi quyết định **có** đáng siết dần lên `--strict` hay không, module
nào trước — không tự quyết ở đây, cần bàn khi tới lượt.

## 2. Việc cần làm (khi bắt đầu, không phải bây giờ)

1. Dựa trên phân loại lỗi theo layer ở `EPIC-002A`, chọn 1 module Domain
   sạch nhất làm thí điểm bật `--strict` riêng cho module đó (mypy hỗ trợ
   cấu hình per-module qua `[[tool.mypy.overrides]]`).
2. Domain layer là ứng viên tự nhiên nhất để bắt đầu: đã theo nguyên tắc
   "Strong Typing & Immutability" của `AGENTS.md` từ trước (annotation đầy
   đủ, `dataclass(frozen=True)`, không `Any`) — nhiều khả năng đã gần đạt
   `--strict` sẵn mà không cần sửa nhiều.
3. Mở rộng dần sang Application, rồi Infrastructure/Presentation (2 layer
   sau có nhiều phụ thuộc bên ngoài — PySide6, SQLAlchemy — dễ cần
   `# type: ignore` có chủ đích hơn là sửa thật).
4. Mỗi module bật `--strict` thành công thì xoá khỏi baseline-suppression
   (nếu `EPIC-002B` có dùng cơ chế đó), không giữ mãi.

## 3. Không thuộc phạm vi task này

Quyết định "có nên đạt `--strict` toàn bộ `src/` hay không, và bao giờ" —
đó là quyết định kiến trúc dài hạn, để ngỏ, bàn lại khi `EPIC-002A`/`B`/`C`
đã xong và có đủ dữ liệu thật để cân nhắc.

---

## 4. Tiến độ thật — danh sách nợ đang co lại (26/08)

> Ghi lại ở đây vì §2 mở đầu bằng "khi bắt đầu, không phải bây giờ". Việc dưới
> đây **không** phải bật `--strict` (vẫn để ngỏ đúng như §3) — nó là phần
> `§2.4`: rút file khỏi baseline-suppression, làm được ngay mà không cần chốt
> quyết định kiến trúc nào.

**Nguồn:** lần chạy thử agent `Scribe` (`.jules/scribe.prompt.md`) sau khi
`EPIC-011` neo prompt của nó vào đúng khối `[tool.mypy]` này. Đo bằng cách bỏ
**toàn bộ** entry per-file rồi chạy đúng lệnh `mypy` mà `ci-local.ps1 -Full`
dùng: **16/25 file còn lỗi thật, 9 file thì không**.

### 9 dòng loại trừ đã hết tác dụng — đã xoá

| Loại | File | Vì sao |
| :--- | :--- | :--- |
| Trỏ vào file **không còn tồn tại** (5) | `scripts/benchmarking/chart_migration_benchmark.py`, `.../native_backtest_chart_interaction_probe.py`, `.../native_chart_camera_probe.py`, `.../native_chart_interaction_probe.py`, `scripts/native_backtest_desktop_e2e.py` | Xoá cùng native chart (`36f3a9f`, xem `BUG-016`). Pattern không khớp file nào |
| File **đã sạch** nhưng chưa ai gạch sổ (4) | `src/application/use_cases/database/repair_data_gap/handler.py`, `src/domain/backtesting/paper_exchange.py`, `src/domain/indicators/rsi.py`, `src/application/use_cases/sync/bulk_sync_market_data/handler.py` | Nợ đã trả, dòng loại trừ vẫn còn → **4 file thật nằm ngoài cổng mà không ai biết** |

Loại thứ hai là rủi ro thật của cơ chế này: một entry không ai đo lại thì đọc
mãi như "nợ", trong khi thực tế nó đang che một file đã sạch khỏi `mypy`.

### +1 file trả nợ thật

`src/infrastructure/binance/market_metadata_parser.py` — xem commit
`refactor(types)` cùng ngày. Lỗi gốc: `float(Any | None)` ở
`min_notional`. Annotate `symbol_info: dict[str, Any]` và `filter_map:
dict[str, dict[str, Any]]` làm lộ tiếp một chỗ thứ hai: filter không có
`filterType` bị lưu dưới key `None` — không lookup nào đọc được. Đã guard;
hành vi không đổi (test đặc tả pass cả trước lẫn sau, đó là bằng chứng).

### +1 nữa qua `DOCTOR-001` (27/08)

`src/application/use_cases/queries/audit_database_integrity/handler.py` — 7 lỗi,
tất cả cùng một lỗi lặp lại ở mỗi chỗ dựng `DataAnomalyDTO`. Không sửa được bằng
một annotation vì có **bảy** chỗ dựng; phải phân rã god method trước rồi mới còn
một chỗ. Xem [`DOCTOR-001`](../../../completed/DOCTOR-001_audit_integrity_handler_rule_extraction.md).

Đáng ghi lại như một mẫu: một entry trong danh sách này có thể **không** phải nợ
kiểu dữ liệu thuần tuý, mà là triệu chứng của một vấn đề cấu trúc. Đo số lỗi
không phân biệt được hai loại — phải đọc.

### Còn lại

**25 → 14 entry per-file.** `src/presentation/` vẫn loại trừ nguyên khối và
**không** thuộc lộ trình này: nó bị chi phối bởi một false positive hệ thống
của PySide6 `@Property`, cần quyết định stub/plugin (§2.3), không phải sửa
từng file.

## 5. Module đầu tiên bật `--strict` thật — `src/domain/` (2026-09-08)

User giao quyền tự quyết ("you will make decision on your own") đúng như §1 dự tính. Làm đúng
theo §2 điểm 1-2: đo trước, không đoán.

### 5.1. Đo baseline

`mypy --strict` chạy cô lập trên `src/domain/` (83 file, trừ 4 file strategy đã biết nợ —
xem §5.3): **chỉ 15 lỗi trên 3 file** — đúng dự đoán §2 điểm 2 ("Domain layer... nhiều khả năng
đã gần đạt `--strict` sẵn mà không cần sửa nhiều").

### 5.2. Sửa thật, không suppress

- `src/domain/strategies/base_strategy.py`, `src/domain/indicator_scripts/base_indicator_script.py`
  (4 lỗi `no-any-return` mỗi file, `input_int`/`input_float`/`input_bool`/`input_string`):
  `InputDeclarations.declare()` trả `Any` một cách có chủ đích — kiểu thật phụ thuộc
  `spec.kind`, và đúng `input_*()` wrapper là nơi DUY NHẤT biết mình vừa khai báo kind nào.
  Bọc `typing.cast(int/float/bool/str, ...)` — phát biểu lại bất biến đã đúng sẵn (`_coerce()`
  raise chứ không bao giờ trả sai kiểu cho đúng `InputKind` đã khai), không phải che giấu gì.
- `base_indicator_script.py` thêm: `_as_series()`/`crossed_above()`/`crossed_below()`/
  `crossed()`/`is_above()`/`is_below()` thiếu hẳn type annotation cho tham số `a`/`b`, và
  `IndicatorHandle` (generic) dùng trần không type argument. Thêm type alias
  `type SeriesLike = IndicatorHandle[Any] | Series` (PEP 695 — file đã dùng cú pháp này cho
  chính `IndicatorHandle[T]`) — `Any` là bound trung thực vì `_as_series()` chỉ đọc `.series`,
  không bao giờ đọc giá trị `T`-typed.
- `src/domain/backtesting/backtest_metrics.py` (1 lỗi `no-any-return`, `_calmar_ratio()`):
  `float ** float` được typeshed gõ lỏng (cơ số âm mũ phân số ra `complex` ở runtime thật).
  Annotate biến trung gian `cagr_percent: float` — phát biểu đúng bất biến miền
  (`end_equity`/`start_equity` luôn không âm trong domain này, kết quả luôn là số thực).

### 5.3. Cấu hình — bài học thật về `strict = true` trong override

`[[tool.mypy.overrides]]` với `strict = true` (thay vì liệt kê từng cờ) **rò rỉ ra ngoài
module đã khớp** — xác nhận bằng chạy thật: lần chạy đầu bắt thêm 27 lỗi `no-untyped-def`/
`no-untyped-call` ở `infrastructure/`/`application/`/`scripts/`, hoàn toàn không khớp pattern
`Sagittarius_Elite_Warrior.src.domain.*`. Sửa bằng cách liệt kê đúng 12 cờ riêng lẻ mà
`--strict` bung ra (đo thật qua `mypy.main.define_options()` trên bản 1.19.1 đang cài, không
chép từ tài liệu — `warn_redundant_casts` bị mypy từ chối làm per-module flag, loại khỏi danh
sách). 4 file strategy còn nợ (§5.4) được giữ ngoài bằng 1 override thứ hai, cụ thể hơn,
đặt SAU override chính — mỗi cờ trả về default không-strict.

### 5.4. Chưa đụng — nợ thật, không phải phạm vi lượt này

4 file `src/domain/strategies/{ema_crossover,ema_trend_pullback,long_term_trend_zone,
multi_ema_trend_follower}_strategy.py` vẫn nằm trong `exclude` khối chính, **chưa** bật
`--strict`: đo riêng cho thấy 29 lỗi thật, khác hẳn lớp lỗi 3 file trên — dict indicator handle
dùng chung trong mỗi strategy suy biến kiểu thành `float | MACDValue | SupportResistanceValue`,
mỗi điểm đọc cần quyết định narrow-kiểu riêng (không phải 1 dòng annotate). Đây là chiến lược
giao dịch thật đang chạy production — sửa vội rủi ro cao hơn lợi ích của lượt này. Để lại đúng
làm tăng tiếp theo của lộ trình (§2 điểm 3: "Mở rộng dần").

### 5.5. Xác minh

Môi trường Linux thật (venv `python3.12` + `Sagittarius_Engine` clone, dựng lại từ `BOT-126`
cùng phiên): thêm 1 hàm thiếu annotation vào `backtest_metrics.py`, xác nhận `mypy` bắt được
ngay (`no-untyped-def`) — chứng minh cờ strict THẬT SỰ có hiệu lực trên domain, không phải cấu
hình chết — rồi gỡ hàm probe đó ra.

- `mypy --config-file pyproject.toml --namespace-packages --explicit-package-bases src scripts`:
  `Success: no issues found in 257 source files`.
- `ruff check`/`ruff format --check` trên các file đổi: sạch.
- `pytest tests/unit/domain/`: **484 passed**.
- `pytest tests/unit/`: **3639 passed**.
- `pytest tests/integration/`: **108 passed, 4 skipped** (skip có sẵn từ trước).
- `pytest tests/sanity/`: **26 passed**.

**File đổi:** `pyproject.toml` (2 override mới), `src/domain/strategies/base_strategy.py`,
`src/domain/indicator_scripts/base_indicator_script.py`, `src/domain/backtesting/backtest_metrics.py`.
Không sửa hành vi runtime nào — toàn bộ thay đổi là annotation/cast/type alias, xác nhận bằng
test suite xanh nguyên vẹn trước/sau.

## 6. Module thứ hai — `src/application/` (2026-09-08, cùng phiên với §5)

Đúng lộ trình §2 điểm 3 ("Mở rộng dần sang Application"). User yêu cầu tiếp tục ("làm tiếp module
tiếp theo") — cùng quyền tự quyết đã giao ở §5.

### 6.1. Đo baseline

`mypy --strict` cô lập trên `src/application/` (126 file): **chỉ 2 lỗi trên 2 file** — sạch hơn cả
Domain.

### 6.2. Sửa thật 1/2 lỗi

`src/application/services/live_strategy_config_store.py::__init__(self, config)` thiếu hẳn type
annotation cho `config`. Cả 2 call site thật (`strategy_arming_coordinator.py`,
`binance_bot_module.py::_arm_from_config`) đều truyền `IConfig` — annotate đúng
`config: IConfig`, không phải suy đoán.

### 6.3. Nợ thật, không sửa trong lượt này

`src/application/use_cases/queries/get_historical_klines/handler.py` — **đã** nằm trong khối
`exclude` chính (nợ baseline có từ `EPIC-002A`, không phải phát hiện mới): `_execute_single()`
truyền thẳng `query.symbol` (kiểu `str | list[str]`) vào `IMarketDataRepository.get_klines()`
(chỉ nhận `str`) — thiếu bước narrow giữa `_execute_single`/`_execute_multi`. Đây là bug tiềm
tàng thật (không phải chỉ artifact của strict), nhưng ngoài phạm vi lượt siết-kiểu này — loại ra
khỏi override strict bằng đúng kỹ thuật đã dùng cho 4 file strategy ở §5.3, để dành sửa riêng.

### 6.4. Xác minh

Cùng quy trình §5.5: tiêm hàm thiếu annotation vào `live_strategy_config_store.py`, xác nhận
`mypy` bắt được (`no-untyped-def`) trước khi gỡ ra.

- `mypy --config-file pyproject.toml --namespace-packages --explicit-package-bases src scripts`:
  `Success: no issues found in 257 source files` — sạch ngay từ lần chạy đầu (không lặp lại lỗi
  rò rỉ `strict = true` của §5.3 vì lần này viết đúng danh sách cờ ngay từ đầu).
- `ruff check`/`ruff format --check`: sạch.
- `pytest tests/unit/`: **3639 passed**.
- `pytest tests/integration/`: **108 passed, 4 skipped**.
- `pytest tests/sanity/`: **26 passed**.

**File đổi:** `pyproject.toml` (2 override mới, cùng khuôn §5.3),
`src/application/services/live_strategy_config_store.py`. Không đổi hành vi runtime.

**Module tiếp theo (chưa làm):** `src/infrastructure/`/`src/presentation/` — theo đúng cảnh báo
sẵn có ở §2 điểm 3, 2 layer này có nhiều phụ thuộc ngoài (PySide6, SQLAlchemy) nên nhiều khả năng
cần `# type: ignore` có chủ đích thay vì sửa thật thuần tuý; `src/presentation/` riêng còn bị
chặn bởi false positive `@Property` đã ghi ở §2.3, cần quyết định stub/plugin trước khi đo được
gì có ý nghĩa.
