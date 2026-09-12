# EPIC-025E — Phase 4: `support/{charting, indicators, ui_kit}`; dissolve `presentation/ui/common/`

- **Status:** 🔴 Backlog
- **Repository:** Elite
- **Blocked by:** D · **Blocks:** F
- **Read first:** HLD §2.3 (a support package is not a bounded context: no business language, no
  business rules allowed), §3.4; ADR D6 (the per-module QML question is reopened here).

## 1. What to do

1. `support/charting/` ← `components/chart_card` (QtWidgets, permanently) plus `IChartHost` and
   the marker / region / info types in `contracts/`.
2. `support/indicators/` ← `domain/indicators`, `indicator_scripts`, `scripting`, plus
   `IIndicatorCatalog`.
3. `support/ui_kit/` ← `kit/`, `qml/kit`, `PageShell`, `DataTable`, the tokens, and the five
   genuinely shared items of `ui/common` (`action_ownership_tracker`, `app_defaults`, `base_feed`,
   `sync_progress_*`).
4. **Delete** `ui/common/`; **delete** `binance_bot_module.py` (now empty); the `settings` screen
   becomes a surface that hangs each module's `settings_section` contribution.
5. Re-decide ADR D6 (per-module QML) with the evidence of the four previous phases.

## 2. Done when

- `ls src/presentation/ui/common` → does not exist; the guard allowlist is **empty**; the two
  layer violations (screens importing `infrastructure/`) are gone.
