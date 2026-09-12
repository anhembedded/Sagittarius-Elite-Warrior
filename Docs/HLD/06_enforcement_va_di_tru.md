# §6 — Enforcement và di trú

## 6.1 Ba guard — architecture fitness function

Luật chỉ sống khi có test (tiền lệ repo: `test_quick_widget_only_in_embed.py`,
`test_only_the_session_factory_constructs_binance_client.py`,
`test_one_event_is_not_subscribed_by_two_presenters.py`). Viết bằng **`ast`**, không regex (`BOT-133`).
Đặt ở `tests/unit/architecture/`.

| Guard | Luật | Allowlist |
| :--- | :--- | :--- |
| `test_module_boundaries.py` | `modules/X/**` chỉ được import: `modules/X/**`, `modules/Y/contracts/**`, `support/*/contracts/**` (+ `support/ui_kit/**`, `support/charting/**` từ `ui/`), `core/**`, Engine, stdlib/3rd-party. `core/**` không import `modules/*`, `support/*`. `support/*` không import `modules/*`. `shell/**` được import mọi `contracts/` + `module.py` | **Ratchet**: file `allowlist_module_boundaries.txt` ghi vi phạm nguyên trạng ở Phase 0; test fail nếu có vi phạm **ngoài** allowlist **hoặc** allowlist chứa dòng đã không còn vi phạm (bắt buộc co) |
| `test_module_domain_is_qt_free.py` | không `PySide6`/`sagittarius_engine.extensions.pyside_mvc` trong `modules/*/{domain,application}`, `core/**`, `support/indicators/**` | không allowlist |
| `test_module_declarations.py` | (a) mọi package trong `modules/` có mặt trong `shell/modules.py` và ngược lại; (b) `dependencies` khai báo == tập module có `contracts/` được import thật (thừa/thiếu đều fail); (c) `register()` không `resolve()` (container spy); (d) không abstract nào bị 2 module claim (`registrations()`) | không allowlist |

Guard layer sẵn có (`architecture-rule` §3) tổng quát hoá theo đường dẫn `modules/*/{domain,
application,adapters,ui}` ở Phase 0 — cùng PR.

**Sanity tier: 0 test mới** (`testing-rule.md` §1). Sanity đã quét "mọi route navigable, mọi screen
package trên đĩa" — surface và module góp `screen` khớp sẵn.

## 6.2 Chỉ số hoàn thành — đo bằng script, ghi vào PR mỗi phase

| Chỉ số | Cách đo | Phase 0 | 1 | 2 | 3 | 4 |
| :--- | :--- | :-: | :-: | :-: | :-: | :-: |
| Tên method trùng `trading` ↔ `dashboard` | script AST so tên method Presenter/VM/View | 59 | **0** | 0 | 0 | 0 |
| Dòng allowlist ranh giới | `wc -l` | N (nguyên trạng) | co | co | co | **0** |
| `presentation/ui/common/` | `ls` | 25 file | 16 | 13 | 12 | **xoá** |
| `binance_bot_module.py` | `wc -l` | < 750 | < 400 | < 250 | < 150 | **xoá** |
| Screen import `infrastructure/` | guard | 2 | 2 | 2 | 1 | **0** |

## 6.3 Di trú — Strangler Fig, Walking Skeleton đi trước (ADR D5)

| Phase | Task | Nội dung | App chạy được? |
| :-: | :--- | :--- | :-: |
| 0 | `EPIC-025A` | `core/`, `shell/`, `BoundedContextModule`, `IContributionRegistry`, 3 guard (allowlist = nguyên trạng), `support/binance_gateway`, **`modules/market_data`** end-to-end | ✅ Data Management + CLI `sync`/`stream` |
| 1 | `EPIC-025B` | `modules/trading`; Trading + Dev Board → surface; `dev_probe` đầu tiên; xoá 59 trùng lặp | ✅ user chạy Testnet: lệnh tay, huỷ, bật/tắt, PnL |
| 2 | `EPIC-025C` | `modules/strategy` (Core); `claim_symbol`; `StrategyContext` chiều đúng | ✅ arm/disarm/tick → lệnh |
| 3 | `EPIC-025D` | `modules/backtesting`; ACL PaperExchange; xoá use case chết | ✅ backtest bit-identical |
| 4 | `EPIC-025E` | `support/{charting,indicators,ui_kit}`; xoá `ui/common`, `binance_bot_module.py`; settings = surface; quyết lại ADR D6 | ✅ |
| 5 | `EPIC-025F` | Engine `EPIC-001D` / `TASK-043`; `ScreenRegistry` → `NavigationService`; conformance suite | ✅ |

Ràng buộc mọi phase: 1 PR; `ci-local.ps1 -Full` xanh (grep log file); **không đổi hành vi nghiệp vụ**
(ngoại lệ đã khai: route mặc định + gate `dev.mode`, §4.2); regression test của `BUG-112/116/117`
vẫn xanh; user tự chạy Testnet sau Phase 1 và 2.

## 6.4 Rủi ro

| Rủi ro | Mức | Xử lý |
| :--- | :-: | :--- |
| `TradingSessionState` mutable, 3 Presenter + 3 handler + thread WS cùng chạm | 🔴 | Phase 1: `trading` sở hữu; ngoài chỉ thấy `TradingSessionSnapshot` + `TradingSessionChangedEvent`; `settings_presenter.py:143` bỏ đọc thẳng |
| ~3.900 test mirror layout cũ | 🟠 | dời theo phase, cùng PR với code; tier giữ nguyên |
| `binance_bot_module.py` god file mới ở `shell/` | 🟠 | mỗi module tự `register()`; `shell/modules.py` chỉ là **danh sách**; guard (a) |
| Engine API mới lệch build cài | 🟡 | `engine_capabilities.py` (`BOT-133`) |
| Scheduler không cancel được job | 🟡 | `PositionRefreshService` tự no-op khi session tắt (đã vậy); ghi nhận cho Engine |
| Ước lượng effort | — | chưa chính xác; chỉ Phase 0 ước được. Đo lại sau Phase 0 |
