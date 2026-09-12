# §5 — Engine nhận mechanism, app giữ policy

User: *"Engine đó sẽ là core engine trong sự nghiệp của tôi, tôi sẽ tái sử dụng cực nhiều."* → mọi thứ
**không biết app này** đi về Engine; mọi thứ biết "trading", "Dev Board", "Binance" ở lại app.
Engine `ui-architecture.md` §1: *"Runtime — Engine owns: Shell, regions, navigation, screen lifecycle"*.

## 5.1 Bảng chia

| Năng lực | Engine (mechanism) | App (policy) | Trạng thái Engine (đo 2026-09-11) |
| :--- | :--- | :--- | :--- |
| Vòng đời module, topo-sort, fail-fast | `IExtension`, `ExtensionDescriptor`, `ExtensionManager` | `BoundedContextModule` (2 hook UI), danh sách module | ✅ có |
| DI | `IContainer`, `registrations()` | kiểm tra double-claim sau `register()` | ✅ có; ⚠️ ghi đè im lặng |
| Event | `IEventBus`, `MemoryEventBus` (sync trên thread caller), `QtEventBridge` (hop sang main thread qua `AutoConnection`) | Feed normalizer / event type | ✅ có |
| CQRS | `IDispatcher` resolve handler từ container (**không có registry**), middleware | Command/Query internal | ✅ có |
| Scheduler / hosted | `Scheduler.every().do()`, `HostedServiceManager` | `PositionRefreshService` job | ✅ có; ⚠️ **không có cancel job** — chỉ `max_runs`/`stop()` |
| Route / stacked navigation | `PresenterManager` (lazy, `QStackedWidget`) | `ScreenRegistry` (`EPIC-016`) | ✅ có — đủ cho Phase 0–4 |
| **Navigation service, regions, slot/contribution registry, screen lifecycle + conformance suite** | **`EPIC-001D`** — `NavigationService`, region, slot registry dạng **model** (không context-property động), `mount/unmount/ui_mode/shutdown`, UI runtime là `IExtension` thật | kind của contribution (§4.3), surface, gate `dev.mode` | ❌ **chưa có** (backlog, P2, B+C đã xong nên **unblocked**) — Phase 5 |
| QML import path per-`QuickSurface` | `create_quick_widget(background=)` — 1 import path hard-code `_QML_IMPORT_PATH` | `QuickSurface` (app-side, `BOT-132`) | ❌ chưa có — cần cho ADR D6 (hoãn) |
| Guard ranh giới import | `import_boundary.find_deep_imports(root, exempt_dirs)` — chỉ soát import sâu vào `pyside_mvc` | 3 guard AST của app | 🟡 có tool hẹp; **tổng quát hoá** thành `find_cross_package_imports(root, rules)` là ứng viên Engine (mọi app dùng modular monolith đều cần) |
| Ordering `QApplication` trước `boot()` | — | composition root dựng `QApplication` trước `App.boot()` | ✅ đã chứng minh bởi `examples/student_management/docs/ui_extension_lifecycle.md`: *"no engine change needed"* |

## 5.2 Task bên Engine (❓ O2 — API cụ thể chốt vòng 2)

Mở **`TASK-043`** bên repo Engine (backlog, tham chiếu `EPIC-001D`), phạm vi tối thiểu mà app này là
consumer thật đầu tiên:

1. `NavigationService`: `navigate(route, *, source: NavigationSource)` phân biệt `USER_INTENT` /
   `RESTORE` (`BUG-104`/`BUG-107` của app: restore không được kích side-effect); `can_leave()` hook.
2. Slot registry: contribution = **descriptor + factory**, expose dạng model theo slot (đúng ràng
   buộc `EPIC-001D`); Engine không biết kind nào tồn tại — kind là chuỗi do app đăng ký.
3. `create_quick_widget(..., import_paths=())` — thêm import path per-widget (mở khoá ADR D6).
4. `import_boundary` tổng quát: luật `(from_package_glob, allowed_import_globs)`, allowlist ratchet.
5. UI runtime thành `IExtension` (đã quyết 2026-08-23 trong `EPIC-001D`).

Mỗi API mới → 1 dòng `RequiredEngineCapability` trong `engine_capabilities.py` của app (`BOT-133`);
Engine bump `b` theo `release.md` (published API đổi).

## 5.3 Cái gì **không** đẩy về Engine

- Kind contribution (`dev_probe`, `settings_section`…): là policy app.
- `BoundedContextModule` 2 hook `contribute`/`subscribe`: giữ ở app tới khi có app thứ hai cần y hệt
  (`architecture-rule` §6.3 — promote khi consumer thứ hai xuất hiện).
- Binance gateway, credentials: app.
