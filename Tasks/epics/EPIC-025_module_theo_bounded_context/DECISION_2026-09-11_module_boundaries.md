# ADR — Ranh giới module theo bounded context, trên Microkernel `IExtension` sẵn có

**Thuộc Epic:** [`EPIC-025`](README.md)
**Nguồn:** [`PRO-004`](../../proposal/PRO-004.md) · HLD chính thức: [`Docs/HLD/`](../../../Docs/HLD/README.md)
**Ngày:** 2026-09-11
**Trạng thái:** 🟢 **Approved — vòng 1** (user chốt trực tiếp trong 2 phiên 2026-09-10 → 11).
Vòng 2 (chi tiết contribution point + API Engine cụ thể) còn 3 câu ❓ ở §3.

> [!IMPORTANT]
> Đọc cột trạng thái, không đọc văn xuôi (khuôn `EPIC-016`'s ADR).
>
> | Nhãn | Ý nghĩa |
> | :--- | :--- |
> | ✅ **Established** | Đã xác nhận trên cây code thật; có `file:line` |
> | 🔵 **Proposed** | Đã chốt trong phiên review; **chưa** implement |
> | 🟢 **User decision** | User quyết trực tiếp, nguyên văn trích trong ngoặc |
> | 🤖 **Agent decision** | User uỷ quyền (*"hãy dựa vào rule tự ra quyết định mà ra quyết định"*) — quyết theo `ONBOARDING.md` §7: pattern có tên, tiền lệ lớn, không sợ redesign |
> | ❓ **Open** | Chặn implementation của phase liên quan cho tới khi trả lời |

---

## 1. Bối cảnh — 3 câu hỏi của user, và 3 dòng bằng chứng đo được

User đặt bài toán bằng đúng 3 câu (2026-09-10): **cắt ở đâu** (macro — DDD chiến lược), **bên trong
mỗi mảnh tổ chức sao** (micro — Clean Architecture), **lắp vào app không biết trước số module thế
nào** (plugin — Microkernel + DIP, Robert Martin's "Main" component). Tiêu chí: *"không ngại đập đi
xây lại, không ngại risk, chỉ sợ bad design, không thể mở rộng, khó bảo trì."*

Bằng chứng đo trên `src/` (664 file / 74.371 dòng), chi tiết ở `PRO-004` §1–§2 và
[`as_is.puml`](../../proposal/PRO-004_assets/as_is.puml):

- Screen import internal của screen khác: **0**. Bệnh **không** phải "import lung tung". ✅
- **59** tên method/thành viên trùng giữa `screens/trading` và `screens/dashboard`; 9 item trong
  `ui/common/` chỉ đúng 2 screen đó dùng. ✅
- `binance_bot_module.py` **750 dòng** là nơi đăng ký duy nhất cho mọi service; không đơn vị code
  nào sở hữu một bounded context — `BUG-117`, `BUG-112`, `BOT-126` là giá đã trả. ✅

---

## 2. Quyết định

### D1 — Cắt theo bounded context; 4 module nghiệp vụ + 3 support + kernel 🟢 User decision

User duyệt bộ tiêu chí cắt (HLD §1, C1–C6) và bản đồ context (HLD §2): *"1. OK"*.

| Loại | Đơn vị | Distillation |
| :--- | :--- | :--- |
| Bounded context | `strategy` | **Core domain** — lý do tồn tại của app |
| Bounded context | `trading`, `market_data`, `backtesting` | Supporting |
| Support (kỹ thuật, không ngôn ngữ nghiệp vụ) | `charting`, `indicators`, `ui_kit` | Generic |
| Kernel service (inject, không bao giờ là module) | DI, bus, config, log, thread, scheduler, navigation, health | — |

`strategy` **tách khỏi** `trading` (giá của việc gộp = `BUG-112`). Account/Equity **cố ý** ở trong
`trading` cho tới khi có consumer thứ hai thật (`architecture-rule.md` §6.3).

### D2 — Hợp đồng module = `IExtension` + `ExtensionDescriptor` của Engine; **không** tạo `IModule` mới 🤖 Agent decision · ✅ Established

Engine đã có `IExtension` (register/boot/shutdown), `ExtensionDescriptor(dependencies,
optional_dependencies, priority)`, `ExtensionManager` topo-sort + fail-fast chu trình + rollback;
`IModule`/`BaseModule` của Engine là **legacy**. Tạo hợp đồng thứ ba = 3 khái niệm module song song
(`IExtension` + `IModule` legacy + `AbstractScreenModule`) — đúng loại bad design user sợ.
Bounded-context module = `IExtension` + 2 hook UI app tự thêm (`contribute`, `subscribe`) — HLD §3.

### D3 — Shell ở lại QtWidgets; danh sách module **tường minh** trong `shell/`; không auto-discovery 🤖 Agent decision · ✅ Established

- `qml-rule.md` §0: *"QML can be nested inside QtWidgets. Qt does not support the reverse"* → shell +
  chart QtWidgets vĩnh viễn. `StackView` trong bản phác gốc → `QStackedWidget` (đã có qua
  `PresenterManager`). Microkernel không đòi shell là QML.
- `EPIC-017` đã từ chối auto-discovery. Danh sách module là **code** trong `shell/` (Martin's
  "Main"), kèm guard 2 chiều: mọi package trong `modules/` phải có mặt trong danh sách và ngược lại.

### D4 — Trading và Dev Board là **hai màn hình chính danh**, cả hai là *composition surface* 🟢 User decision

Nguyên văn: *"Trading là màn hình use-case thật, còn Dev Board chỉ là màn hình để developer test and
discover API. Nên có nhiều cái tụi nó sẽ trùng lặp."* Và: *"'discover API' → có nghĩa là khi bạn dev
nếu API nào của sàn chưa rõ, thì sẽ tạo 1 UI để test API đó."*

Hệ quả thiết kế (HLD §4):
- **Không** màn nào chứa logic nghiệp vụ. Cả hai *bố cục* widget do module **góp** vào; đúng một bản
  `_run_enable`, một `LiveOrderBookCoordinator`, một chủ sở hữu read-model vị thế.
- Dev Board gate bằng `dev.mode`, có thêm contribution point **`dev_probe`**: module nào cần khám phá
  một API sàn chưa rõ thì góp một widget probe (gọi đúng port/adapter thật của module đó, hiển thị
  request/response thô). Probe là code **của module** (`modules/X/ui/dev_probes/`), không phải của
  Dev Board — Dev Board chỉ là nơi treo.
- 59 chỗ trùng lặp → 0 là **tiêu chí hoàn thành** của Phase 1, đo bằng script, không bằng cảm nhận.

### D5 — Thứ tự di trú: Walking Skeleton bên trong Strangler Fig 🤖 Agent decision

User: *"Tôi không chắc, tôi đâu có bỏ công điều tra, bạn mới là người làm việc đó."*

| Phase | Nội dung | Vì sao ở vị trí này |
| :-: | :--- | :--- |
| 0 | Cơ chế: `core/`, `BoundedContextModule`, `IContributionRegistry`, 3 guard (allowlist = nguyên trạng), `shell/` liệt kê module; **+ `modules/market_data`** | Walking Skeleton: `market_data` là context **mỏng nhất chạm đủ mọi kênh** (persistence, REST, WS, 1 screen, CLI) → chứng minh pattern end-to-end với ít rủi ro nhất |
| 1 | `modules/trading` + Trading/Dev Board thành surface | Gỡ 59 chỗ trùng lặp sớm nhất; là nơi bug thật đang phát sinh (`BUG-111`→`117`) |
| 2 | `modules/strategy` | Core domain, tách khỏi trading đã thành surface |
| 3 | `modules/backtesting` (12.309 dòng UI) | Chỉ phụ thuộc `contracts/` của `market_data` + `strategy` |
| 4 | `support/{charting,indicators,ui_kit}`; `ui/common/` giải thể | Sau khi mọi consumer đã là module |
| 5 | Engine `EPIC-001D` (`NavigationService`, regions, screen lifecycle) | Phase 0–4 **không cần** navigation mới — `ScreenRegistry` hiện tại đủ |

Mỗi phase = 1 PR, CI xanh, app **chạy được** (kênh phát hiện bug hiệu quả nhất là user tự chạy
Testnet — không được mất nó).

### D6 — QML per-module: **hoãn**, giữ `src/presentation/ui/qml/` là nơi chính thức 🔵 Proposed

Cho phép module sở hữu QML cần (a) sửa tường minh `qml-rule.md` §0.2 (tiền lệ `EPIC-003`), (b) cơ
chế import-path per-`QuickSurface` bên Engine (hiện mỗi `QQuickWidget` tự tạo `QQmlEngine` trong
`create_quick_widget()`, một import path hard-code). Chưa có consumer nào bị chặn vì thiếu nó →
mở lại ở Phase 4/5 khi Engine làm `EPIC-001D`. Trong lúc đó: Python wrapper của widget nằm trong
module; file `.qml` vẫn ở `qml/<Widget>/`.

### D7 — Test giữ theo **tier** (`tests/{unit,integration,sanity}`), bên trong mirror đường dẫn module 🤖 Agent decision

Cả `ci-local.ps1`, `testing-rule.md` và tầng sanity đều xây trên tier. Colocate `modules/X/tests/`
chỉ có lợi khi module thật sự rời repo — chưa có nhu cầu. Thay đổi này **đảo ngược được** sau, và
không chặn phase nào. Sanity **không thêm test mới** (`testing-rule.md` §1).

### D8 — `EPIC-024C` bị hấp thu vào `EPIC-025` → `cancelled/` 🔵 Proposed

Phạm vi 024C (Market Connector / Market Order / Strategy Engine) là **tập con** của D1; làm riêng =
dựng cơ chế module 2 lần (`ONBOARDING.md` §12.5.1 cấm). Lý do ghi ở đầu file 024C.

### D9 — `core/vo` gọi là **Published Language**, không phải "Shared Kernel" ✅ Established

`architecture-rule.md` định nghĩa Shared Kernel **= đúng 2 symbol Engine** (`IDomainEvent`,
`BaseEvent`), có test khoá. Dùng lại từ đó cho nghĩa khác sẽ phá luật đang có. Luật vào `core/`:
chưa có ≥2 consumer ở 2 module khác nhau thì không được vào.

### D10 — Engine nhận **mechanism**, app giữ **policy** 🟢 User decision + ✅ Established

User: *"Tôi muốn Engine hỗ trợ scalable nhiều context/screen, vì Engine đó sẽ là core engine trong
sự nghiệp của tôi, tôi sẽ tái sử dụng cực nhiều."* Engine `ui-architecture.md` §1: *"Runtime —
Engine owns: Shell, regions, navigation, screen lifecycle"*; `EPIC-001D` (backlog) đã lên kế hoạch
đúng việc này từ 2026-08-23. Không dựng bản song song phía app. Mỗi API Engine mới → một dòng trong
`engine_capabilities.py` (`BOT-133`). Bảng chia cụ thể: HLD §5.

### D11 — Enforcement: 3 guard AST, allowlist **chỉ được co** 🔵 Proposed

`test_module_boundaries.py`, `test_module_domain_is_qt_free.py`, `test_core_has_no_module_imports.py`
— viết bằng `ast` (bài học `BOT-133`: regex đỏ trên chính tài liệu của API). Allowlist vi phạm nguyên
trạng ghi ở Phase 0; mỗi phase co lại; test fail nếu nở ra.

### D12 — Ràng buộc di trú: refactor thuần, không đổi hành vi nghiệp vụ ✅ Established

Kế thừa `EPIC-024C` §4: *"modularize là đổi ranh giới code, không đổi logic nghiệp vụ"*. Coordinator
vẫn do Presenter sở hữu, inject qua constructor — không DI-discovered (`async-ui-action-rule.md` §2).

---

## 3. Còn mở — chặn phase nào

| # | Câu hỏi | Chặn | Trả lời ở |
| :-: | :--- | :-: | :--- |
| ❓ O1 | Danh sách **cuối** các contribution point kind và schema từng kind | Phase 0 (`IContributionRegistry`) | Vòng 2 — HLD §4 hiện là bản nháp |
| ❓ O2 | API Engine cụ thể cho `NavigationService`/regions (`EPIC-001D`) | Phase 5 | Vòng 2 — task bên Engine |
| ❓ O3 | QML per-module (D6) | Không chặn | Phase 4/5 |

---

## 4. Hệ quả

- `binance_bot_module.py` teo dần thành **danh sách module** trong `shell/` — không còn là god file.
- `presentation/ui/common/` **biến mất** ở Phase 4: 9 item "chỉ trading+dashboard dùng" về
  `modules/trading` / `modules/strategy`; 5 item dùng chung thật về `support/ui_kit` hoặc kernel.
- `EPIC-016`'s `ScreenRegistry`/`AbstractScreenModule` **giữ nguyên** cho tới Phase 5 — module góp
  screen qua đúng cơ chế đó.
