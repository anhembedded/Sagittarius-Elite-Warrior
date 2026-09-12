# §4 — Surfaces and contribution points

## 4.1 The problem, measured

Trading (`screens/trading`) and Dev Board (`screens/dashboard`) build **one** set of business
behaviour twice. Fifty-nine method and member names are duplicated between them; both use the
same `PositionsPanel` and `OpenOrdersPanel`; the equity chart is built with the same recipe (a
comment says so: *"same construction recipe"*); the strategy card has the same eight object names
in both; the session card and last-signal card docstrings say *"mirrors"*. `DashboardPresenter` is
2,008 lines long, `TradingPresenter` 973.

The user's decision (ADR D4) is that Trading is the real use-case screen and Dev Board is the
developer's screen for **testing** and **discovering APIs** — in the user's words, *"nên có nhiều
cái tụi nó sẽ trùng lặp"* ("so a lot of what they show will overlap"). Overlap is **intended**. The
design requirement is that the overlap be produced by **one** widget used in two places, not by two
copies of the widget.

## 4.2 A surface is a screen with no business logic

A **surface** is a screen under `shell/surfaces/<id>/` that does exactly three things: (1) lays
itself out (a `PageShell` with named slots), (2) asks the `IContributionRegistry` "who contributes
what into which of my slots", and (3) builds each widget through the factory the module provided.
It contains **zero lines of business logic, zero business Coordinators and zero Feeds** — all of
that lives inside the widgets that modules own.

| Surface | Slots | Gate | Default route |
| :--- | :--- | :--- | :--- |
| `trading` | `header` · `context_bar` · `workspace` (chart) · `rail` (cards) · `console` | always | ✅ **default** 🔵 (today Dev Board has `is_default=True`) |
| `dev_board` | `header` · `system_controls` · `workspace` (several charts) · `rail` · `probes` 🔵 · `console` | **`dev.mode`** 🔵 (today it is **not gated**; measured, `dev.mode` is read only by the asset validator, the log filter and the FPS overlay) | no |
| `settings` | `sections` | always | no |

⚠️ These are two changes in **user-visible behaviour**, not pure refactoring: the default route
becomes Trading, and Dev Board is hidden when `dev.mode` is false. They are stated here so the user
sees them before they happen; each can be reversed with a one-line configuration change.

**A widget contributed to a surface belongs to a module.** For example, `trading` contributes the
`PositionsPanel` factory to both `trading.rail` and `dev_board.rail` — one class, two instances,
one `LiveOrderBookCoordinator` (in `modules/trading/ui/`). Duplication drops to zero because there
is nothing left to copy.

## 4.3 Contribution points — the round-1 kinds (❓ O1: the final schema is settled in round 2)

The mechanism: a module declares a **description** (a frozen dataclass descriptor) plus a factory;
the surface or shell renders it. The principles are borrowed from the Engine's `EPIC-001D`: *"Python
describes, QML renders"*, *"the registry is for genuinely dynamic surfaces"*, *"regions decide
geometry"*.

| Kind | Descriptor (draft) | Contributed by | Rendered by | Replaces today |
| :--- | :--- | :--- | :--- | :--- |
| `screen` | `route, title, icon, section_key, sequences, is_default, factory(container) -> (View, Presenter)` | every module | the shell (`ScreenRegistry` ✅ from `EPIC-016` — kept until Phase 5) | the hard-coded tuple of 5 modules at `app_bootstrapper.py:322` |
| `surface_widget` | `surface_id, slot, order, factory(container) -> QWidget, owner_module` | market_data, trading, strategy, charting, indicators | a surface | two Presenters building their own cards |
| `settings_section` | `title, order, factory(container) -> QWidget` (a form bound to the **module's own** config keys) | trading (venue, credentials check, limits), market_data (venue, default symbols / interval / sync days), ui_kit (theme) | the `settings` surface | a single `SettingsView` grid that knows every config key |
| `dev_probe` 🔵 | `title, module_id, factory(container) -> QWidget` | any module with an exchange API it does not yet understand | the `dev_board.probes` slot, only under `dev.mode` | **nothing** (measured: the app has no probe or raw-endpoint UI at all) |
| `cli_command` | `name, build_parser(sub), execute(app, args)` | market_data (`sync`, `stream`), trading (`exchange-status`, `order-preview`, `order-dry-run`), strategy (`trade-once`) | `shell/cli` | the if/elif chain at `main.py:139-156` plus `cli_commands.json` |
| `status_tile` | `key, factory -> QWidget` | trading (websocket pill), market_data (price ticker) | a surface header | `DevBoardPanel.header_actions` |

**Considered and not adopted in round 1.** `chart_overlay`: drawing on a chart goes through
`IChartHost`, the port of `support/charting`, which the surface hands to the widget; no separate
registry is needed yet. `health_tile`: folded into `status_tile`.

## 4.4 `dev_probe` — what "discovering an API" means, concretely

The user's definition: *"khi bạn dev nếu API nào của sàn chưa rõ, thì sẽ tạo 1 UI để test API đó"*
("while developing, if some exchange API is unclear, you build a UI to try that API out").

- A probe is **module code** (`modules/<id>/ui/dev_probes/<name>_probe.py`). It calls the module's
  **real adapter or port** — never the raw SDK; the guard *only the session factory constructs
  binance client* still applies — and shows the request that was sent, the raw response, and the
  translated error. It is living evidence of "how this API behaves" gathered before a use case is
  written against it.
- A probe's lifetime is **temporary**. Once the API is understood and the use case has tests, the
  probe is either deleted or kept deliberately as an operational tool; that choice is made in the
  pull request and written into the task. A probe must not become an unannounced feature.
- The first probe (Phase 1, `trading`) is an "Exchange API tester": pick an endpoint from the list
  the adapter already wraps (`positionRisk`, `openOrders`, the `exchangeInfo` filters for one symbol,
  `listenKey`), press the button, read the payload. This is exactly what was missing during the
  `BUG-117` investigation, where the only option was reading logs instead of calling the endpoint.
- No probe is loaded when `dev.mode` is false: the `dev_board` surface does not exist, so its
  factories never run.

## 4.5 Who owns which widget (Trading and Dev Board)

| Widget | Owning module | Trading | Dev Board |
| :--- | :--- | :-: | :-: |
| Chart card (one symbol) / chart list (n symbols) | `charting` (host) + `market_data` (feed) | 1 | n |
| Positions table, open orders table (with cancel-one-order) | `trading` | ✅ | ✅ |
| Manual order card | `trading` | 🔵 (today Dev Board only — the user decides whether Trading gets it; the mechanism allows it with one line) | ✅ |
| Session card, Enable/Disable, Emergency stop, websocket pill | `trading` | ✅ | ✅ |
| Equity chart | `trading` (adapter) + `charting` | ✅ | ✅ |
| Strategy card, last-signal card, parameters dialog | `strategy` | ✅ | ✅ |
| Strategy overlay on the chart | `strategy` | ✅ | 🔵 |
| Indicator script checklist | `indicators` | — | ✅ |
| System controls (market / symbol / date range / load / start / stop), symbol picker | `market_data` | a reduced context bar | ✅ |
| API probes | each module | — | ✅ |
| Log console | `ui_kit` | ✅ | ✅ |
