# EPIC-025A — Phase 0: cơ chế module + `modules/market_data` (Walking Skeleton)

- **Trạng thái:** 🔴 Backlog — **chặn bởi ❓ O1** (ADR §3: schema các contribution point kind)
- **Repo:** Elite
- **Chặn:** B, C, D, E
- **Đọc trước:** HLD §1–§3 (tiêu chí cắt, context map, contracts của `market_data`), §4 (contribution
  point), §6 (guard); ADR D2, D3, D5, D9, D11.

## 1. Việc cần làm

**Cơ chế (không di trú gì ngoài `market_data`):**

1. `src/core/` — `core/contracts/` (hợp đồng kernel phía app: `IContributionRegistry`, các
   `Contribution*` descriptor) + `core/vo/` (Published Language: chỉ value object trung tính đã có
   ≥2 consumer ở 2 module — HLD §2.4).
2. `src/shell/` — Martin's "Main": `modules.py` liệt kê tường minh các `BoundedContextModule`;
   `create_app()` chuyển từ `src/main.py`; `binance_bot_module.py` **chưa xoá** ở phase này, chỉ
   bớt phần `market_data`.
3. `BoundedContextModule(IExtension)` (HLD §3.1) + `IContributionRegistry` (HLD §4).
4. 3 guard AST `tests/unit/architecture/`: `test_module_boundaries.py` (allowlist **= nguyên trạng**,
   chỉ được co), `test_module_domain_is_qt_free.py`, `test_core_has_no_module_imports.py`; guard 2
   chiều danh sách module ↔ `modules/` trên đĩa.
5. Bỏ tuple hard-code 5 screen module ở `app_bootstrapper.py` → shell lấy từ contribution `screen`.

**Walking Skeleton — `modules/market_data/`** (HLD §3.2): `domain/` (Kline, Symbol catalog, shard,
gap, coverage, `MarketDataVenue`), `application/` (use case `sync/`, `database/`, query klines,
stream thị trường), `contracts/` (`IHistoricalKlines`, `ISymbolCatalog`, `IMarketStream`, DTO,
event `MarketTickEvent`/`CandleClosedEvent`), `adapters/` (`persistence/`, `binance/market/`),
`ui/` (screen Data Management + Python wrapper widget; `.qml` **vẫn** ở `qml/`), CLI `sync`/`stream`.

## 2. Xong khi

- App chạy y như cũ; Data Management đi qua registry; CLI `sync`/`stream` chạy.
- Allowlist guard co lại đúng phần `market_data`; `ci-local.ps1 -Full` xanh (grep log file).
- Sanity **0** test mới.
