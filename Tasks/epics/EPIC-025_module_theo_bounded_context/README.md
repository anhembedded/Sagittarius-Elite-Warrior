# EPIC-025 — Tách app thành module theo bounded context, trên Microkernel `IExtension` của Engine

- **Trạng thái:** 🔴 Backlog — vòng spec 1 xong (2026-09-11); **chưa task con nào được bắt đầu**
  trước khi ❓ O1 trong [ADR](DECISION_2026-09-11_module_boundaries.md) §3 được trả lời (vòng 2).
- **Repo:** Elite (Phase 0–4) · Engine (Phase 5, task riêng bên repo Engine tham chiếu `EPIC-001D`)
- **Nguồn gốc:** [`PRO-004`](../../proposal/PRO-004.md) — user (2026-09-10): *"hiện tại chúng ta
  không có chia module theo kiểu DDD, nên mọi thứ đang rất là lung tung và đạp chân lẫn nhau. Tui
  muốn redesign lại khá lớn."* Tiêu chí: *"không ngại đập đi xây lại, không ngại risk, chỉ sợ bad
  design, không thể mở rộng, khó bảo trì."*
- **Kim chỉ nam:** [`Docs/HLD/`](../../../Docs/HLD/README.md) — High-Level Design chính thức. Epic
  này chỉ tóm tắt quyết định và chia phase; **không lặp lại** phân tích/bằng chứng. Mọi task con đọc
  HLD + ADR trước.
- **Hấp thu:** [`EPIC-024C`](../EPIC-024_modularize_trading_core_va_giao_dich_thu_cong/cancelled/EPIC-024C_modularize_trading_core.md) (huỷ 2026-09-11, lý do đầu file đó).

---

## 1. Quyết định đã chốt (đầy đủ ở ADR D1–D12)

1. **4 bounded context** `market_data` / `trading` / `strategy` (Core) / `backtesting` + **3 support**
   `charting` / `indicators` / `ui_kit` + kernel service. Trading và Dev Board là **hai màn hình chính
   danh**, cả hai là *composition surface* của widget do module góp; Dev Board gate `dev.mode`, có
   thêm contribution point `dev_probe` để khám phá API sàn chưa rõ.
2. **Module = `IExtension` của Engine** + 2 hook UI (`contribute`, `subscribe`). Không `IModule` mới.
3. **Shell QtWidgets, danh sách module tường minh trong `shell/`**, không auto-discovery.
4. **Walking Skeleton trong Strangler Fig**: `market_data` đi cùng cơ chế ở Phase 0; `trading` ngay
   sau vì đó là nơi 59 chỗ trùng lặp và bug thật đang ở.
5. **Engine nhận mechanism, app giữ policy**; mỗi API Engine mới → `engine_capabilities.py`.

## 2. Mục tiêu — đo được

| Chỉ số | Hôm nay (đo 2026-09-10) | Khi epic xong |
| :--- | :--- | :--- |
| Tên method/thành viên trùng giữa `screens/trading` ↔ `screens/dashboard` | **59** | **0** |
| Item trong `presentation/ui/common/` | 25 file / 2.015 dòng | thư mục **không còn** |
| Dòng của composition root (`binance_bot_module.py`) | 750 | danh sách module trong `shell/`, ≤ 100 |
| Screen import `infrastructure/**` (vi phạm `architecture-rule` §3) | 2 | 0 |
| Allowlist vi phạm ranh giới module (guard `test_module_boundaries.py`) | = nguyên trạng ở Phase 0 | **rỗng** |
| Test sanity thêm mới | — | **0** (`testing-rule.md` §1) |

## 3. Thứ tự thực hiện

Mỗi phase = **1 PR**, CI xanh, **app chạy được** (user tự chạy Testnet là kênh phát hiện bug hiệu
quả nhất — không được mất). Không đổi hành vi nghiệp vụ (ADR D12).

| # | Task | Chặn bởi | Trạng thái |
| :-: | :--- | :--- | :---: |
| **A** | [Phase 0 — Cơ chế + `modules/market_data` (Walking Skeleton)](incomplete/EPIC-025A_phase0_co_che_va_market_data.md) | ❓ O1 (vòng 2) | 🔴 |
| **B** | [Phase 1 — `modules/trading`; Trading + Dev Board thành surface](incomplete/EPIC-025B_phase1_trading_va_surface.md) | A | 🔴 |
| **C** | [Phase 2 — `modules/strategy` (Core domain)](incomplete/EPIC-025C_phase2_strategy.md) | B | 🔴 |
| **D** | [Phase 3 — `modules/backtesting`](incomplete/EPIC-025D_phase3_backtesting.md) | C | 🔴 |
| **E** | [Phase 4 — `support/*`; giải thể `ui/common/`](incomplete/EPIC-025E_phase4_support_va_giai_the_common.md) | D | 🔴 |
| **F** | [Phase 5 — Engine `EPIC-001D`: `NavigationService`, regions, screen lifecycle](incomplete/EPIC-025F_phase5_engine_navigation.md) | E · task bên Engine | 🔴 |

## 4. Ngoài phạm vi, cố ý

- Không microservice / multi-process; không hot-reload; không plugin bên thứ ba (mọi module
  first-party → không semver contract public).
- Không 1 DB / 1 module — chung SQLite, mỗi module sở hữu **schema namespace**.
- Không đổi `EPIC-016`'s `ScreenRegistry`/`AbstractScreenModule` trước Phase 5.
- QML per-module: hoãn (ADR D6).
