# EPIC-025F — Phase 5: dựng trên Engine `EPIC-001D` (`NavigationService`, regions, screen lifecycle)

- **Trạng thái:** 🔴 Backlog — **chặn bởi ❓ O2** (ADR §3) và task bên repo Engine
- **Repo:** Elite (consumer) · Engine (mechanism — task riêng, tham chiếu `EPIC-001D`)
- **Chặn bởi:** E
- **Đọc trước:** HLD §5 (bảng chia Engine/app); Engine `Tasks/epics/EPIC-001_ui_engine_foundation/
  EPIC-001D_runtime_slot_registry.md`; `examples/student_management/docs/ui_extension_lifecycle.md`
  bên Engine (ordering `QApplication` trước `boot()`).

## 1. Việc cần làm (phía app)

1. Thay `ScreenRegistry` (`EPIC-016`) bằng `NavigationService` của Engine: route từ contribution
   `screen`; phân biệt `restore_route` ≠ `user_intent_to_navigate` (`BUG-104`/`BUG-107`);
   `can_leave()` guard cho action đang bay (`async-ui-action-rule` §1).
2. `IContributionRegistry` của app đứng trên slot registry của Engine (app giữ **kind** = policy).
3. Mỗi API Engine mới → `engine_capabilities.py` (`BOT-133`).
4. Conformance suite screen của Engine chạy trên **mọi** surface của app.

## 2. Xong khi

- `main_window.py` không import screen nào; navigation dựng hoàn toàn từ self-description.
