# EPIC-025E — Phase 4: `support/{charting,indicators,ui_kit}`; giải thể `presentation/ui/common/`

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** D · **Chặn:** F
- **Đọc trước:** HLD §2.3 (support ≠ bounded context: không ngôn ngữ nghiệp vụ, cấm rule nghiệp vụ),
  §3.6; ADR D6 (mở lại câu QML per-module ở đây).

## 1. Việc cần làm

1. `support/charting/` ← `components/chart_card` (QtWidgets vĩnh viễn) + `IChartHost`,
   `IOverlayRegistry` trong `contracts/`.
2. `support/indicators/` ← `domain/indicators`, `indicator_scripts`, `scripting` + `IIndicatorCatalog`.
3. `support/ui_kit/` ← `kit/`, `qml/kit`, `PageShell`, `DataTable`, tokens, 5 item dùng chung thật
   của `ui/common` (`action_ownership_tracker`, `app_defaults`, `base_feed`, `sync_progress_*`).
4. `ui/common/` **xoá**; `binance_bot_module.py` **xoá** (đã rỗng); `settings` thành surface treo
   contribution `settings_section` của từng module.
5. Quyết định lại ADR D6 (QML per-module) với bằng chứng của 4 phase trước.

## 2. Xong khi

- `ls src/presentation/ui/common` → không tồn tại; allowlist guard **rỗng**; 2 vi phạm §3 → 0.
