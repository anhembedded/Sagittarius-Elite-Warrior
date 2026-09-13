# ADR — Module boundaries by bounded context, on the Engine's existing `IExtension` microkernel

**Epic:** [`EPIC-025`](README.md)
**Source:** [`PRO-004`](../../proposal/PRO-004.md) · The official design: [`Docs/HLD/`](../../../Docs/HLD/README.md)
**Date:** 2026-09-11
**Status:** 🟢 **Approved — round 1** (decided directly by the user across the sessions of
2026-09-10 and 2026-09-11). Round 2 (contribution-point detail and the concrete Engine API) still
has the three open questions in §3.

> [!IMPORTANT]
> Read the status column, not the prose (the convention of `EPIC-016`'s ADR).
>
> | Label | Meaning |
> | :--- | :--- |
> | ✅ **Established** | Confirmed on the real code tree; cited as `file:line` |
> | 🔵 **Proposed** | Settled in the review session; **not yet** implemented |
> | 🟢 **User decision** | Decided by the user directly; quoted verbatim, then translated |
> | 🤖 **Agent decision** | Delegated by the user (*"hãy dựa vào rule tự ra quyết định mà ra quyết định"* — "decide it yourself, based on the decision rule") and decided under `ONBOARDING.md` §7: a named pattern, broad precedent, no fear of redesign |
> | ❓ **Open** | Blocks the implementation of the phase named alongside until answered |

---

## 1. Context — the user's three questions and three lines of measured evidence

The user posed the problem as exactly three questions (2026-09-10): **where to cut** (macro —
strategic DDD), **how each piece is organised inside** (micro — Clean Architecture), and **how to
plug pieces into an application whose number of modules is not known in advance** (plugin —
Microkernel and the Dependency Inversion Principle; Robert Martin's "Main" component). The
acceptance criterion, verbatim: *"không ngại đập đi xây lại, không ngại risk, chỉ sợ bad design,
không thể mở rộng, khó bảo trì"* ("not afraid to tear down and rebuild, not afraid of risk; only
afraid of bad design, of not being able to extend, of being hard to maintain").

Evidence measured on `src/` (664 files, 74,371 lines), detailed in `PRO-004` §1–§2 and drawn in
[`as_is.puml`](../../proposal/PRO-004_assets/as_is.puml):

- Screens importing another screen's internals: **0**. The disease is **not** "imports everywhere". ✅
- **59** method and member names duplicated between `screens/trading` and `screens/dashboard`; 9
  items in `ui/common/` are used by exactly those two screens. ✅
- `binance_bot_module.py` is **750 lines** and the only registration point for every service; no
  unit of code owns a bounded context. `BUG-117`, `BUG-112` and `BOT-126` are the price already
  paid. ✅

---

## 2. Decisions

### D1 — Cut by bounded context: four business modules, three support packages, a kernel 🟢 User decision

The user approved the cutting criteria (HLD §1, C1–C6) and the context map (HLD §2): *"1. OK"*.

| Kind | Unit | Distillation |
| :--- | :--- | :--- |
| Bounded context | `strategy` | **Core domain** — the reason the app exists |
| Bounded context | `trading`, `market_data`, `backtesting` | Supporting |
| Support (technical, no business language) | `charting`, `indicators`, `ui_kit`, `binance_gateway` | Generic |
| Kernel service (injected, never a module) | DI, bus, config, log, threads, scheduler, navigation, health | — |

`strategy` is **separated from** `trading`; the cost of keeping them merged was `BUG-112`.
Account/Equity **deliberately** stays inside `trading` until a second real consumer appears
(`architecture-rule.md` §6.3).

### D2 — The module contract is the Engine's `IExtension` + `ExtensionDescriptor`; **no** new `IModule` 🤖 Agent decision · ✅ Established

The Engine already has `IExtension` (register / boot / shutdown), `ExtensionDescriptor(dependencies,
optional_dependencies, priority)` and an `ExtensionManager` with topological sort, fail-fast on
cycles and rollback; the Engine's own `IModule` / `BaseModule` are **legacy**. A third contract
would mean three module concepts side by side (`IExtension`, the legacy `IModule`,
`AbstractScreenModule`) — exactly the kind of bad design the user fears. A bounded-context module is
an `IExtension` plus two application-side UI hooks (`contribute`, `subscribe`) — HLD §3.1.

### D3 — The shell stays QtWidgets; the module list is **explicit** in `shell/`; no auto-discovery 🤖 Agent decision · ✅ Established

- `qml-rule.md` §0: *"QML can be nested inside QtWidgets. Qt does not support the reverse"* — the
  shell and the chart are QtWidgets permanently. The `StackView` of the original sketch becomes
  `QStackedWidget` (already present through `PresenterManager`). A microkernel does not require a
  QML shell.
- `EPIC-017` rejected auto-discovery. The module list is **code** in `shell/` (Martin's "Main"),
  with a two-way guard: every package under `modules/` is in the list, and every list entry exists
  on disk.

### D4 — Trading and Dev Board are **two legitimate screens**, and both are *composition surfaces* 🟢 User decision

Verbatim: *"Trading là màn hình use-case thật, còn Dev Board chỉ là màn hình để developer test and
discover API. Nên có nhiều cái tụi nó sẽ trùng lặp."* ("Trading is the real use-case screen; Dev
Board is only the screen where the developer tests and discovers APIs. So a lot of what they show
will overlap.") And: *"'discover API' → có nghĩa là khi bạn dev nếu API nào của sàn chưa rõ, thì sẽ
tạo 1 UI để test API đó."* ("'discover API' means: while developing, if some exchange API is
unclear, you build a UI to try that API out.")

Design consequences (HLD §4):
- **Neither** screen contains business logic. Both *lay out* widgets that modules **contribute**;
  there is one `_run_enable`, one `LiveOrderBookCoordinator`, one owner of the positions read model.
- Dev Board is gated by `dev.mode` and gains a contribution point **`dev_probe`**: a module that
  needs to explore an unclear exchange API contributes a probe widget that calls the module's own
  real port or adapter and shows the raw request and response. A probe is **the module's** code
  (`modules/X/ui/dev_probes/`), not Dev Board's — Dev Board is only where it hangs.
- "59 duplicates → 0" is the **completion criterion** of Phase 1, measured by a script, not by
  impression.

### D5 — Migration order: a Walking Skeleton inside a Strangler Fig 🤖 Agent decision

The user: *"Tôi không chắc, tôi đâu có bỏ công điều tra, bạn mới là người làm việc đó."* ("I am not
sure — I did not do the investigation, you did.")

| Phase | Content | Why here |
| :-: | :--- | :--- |
| 0 | Mechanism: `core/`, `BoundedContextModule`, `IContributionRegistry`, the three guards (allowlist as found), `shell/` listing the modules; **plus `modules/market_data`** | Walking Skeleton: `market_data` is the **thinnest context that touches every channel** (persistence, REST, websocket, one screen, CLI), so it proves the pattern end to end at the lowest risk |
| 1 | `modules/trading`; Trading and Dev Board become surfaces | Removes the 59 duplicates earliest; it is where real bugs are being found (`BUG-111` → `117`) |
| 2 | `modules/strategy` | The Core domain, separated from a `trading` that is already a surface |
| 3 | `modules/backtesting` (12,309 lines of UI) | Depends only on the `contracts/` of `market_data` and `strategy` |
| 4 | `support/{charting, indicators, ui_kit}`; `ui/common/` dissolved | After every consumer is a module |
| 5 | Engine `EPIC-001D` (`NavigationService`, regions, screen lifecycle) | Phases 0–4 **do not need** new navigation — today's `ScreenRegistry` suffices |

Each phase is one pull request, with CI green and the app **running** (the most effective bug
channel is the user running Testnet; it must not be lost).

### D6 — Per-module QML: **deferred**; `src/presentation/ui/qml/` remains the official place 🔵 Proposed

Letting a module own its QML requires (a) an explicit amendment of `qml-rule.md` §0.2 (the
`EPIC-003` precedent for amending a rule) and (b) a per-`QuickSurface` import-path mechanism on the
Engine side (today each `QQuickWidget` creates its own `QQmlEngine` inside `create_quick_widget()`
with one hard-coded import path). No consumer is blocked by its absence → revisit in Phase 4/5 when
the Engine does `EPIC-001D`. Meanwhile: a widget's Python wrapper lives in the module; the `.qml`
file stays under `qml/<Widget>/`.

### D7 — Tests stay organised by **tier** (`tests/{unit, integration, sanity}`), mirroring the module path inside each tier 🤖 Agent decision

`ci-local.ps1`, `testing-rule.md` and the sanity tier are all built on tiers. Co-locating
`modules/X/tests/` pays off only when a module really leaves the repository, which nothing needs
yet. The choice is **reversible** later and blocks no phase. The sanity tier **gains no tests**
(`testing-rule.md` §1).

### D8 — `EPIC-024C` is absorbed into `EPIC-025` → `cancelled/` 🔵 Proposed

The scope of 024C (Market Connector / Market Order / Strategy Engine) is a **subset** of D1; doing
it separately would build the module mechanism twice (`ONBOARDING.md` §12.5.1 forbids that). The
reason is written at the top of the 024C file.

### D9 — `core/vo` is called a **Published Language**, not a "Shared Kernel" ✅ Established

`architecture-rule.md` defines the Shared Kernel as **exactly two Engine symbols** (`IDomainEvent`,
`BaseEvent`), and a test locks that. Reusing the term for something else would break a rule that
is already enforced. Admission to `core/`: only a type with at least two consumers in two different
modules.

### D10 — The Engine receives **mechanism**, the application keeps **policy** 🟢 User decision + ✅ Established

The user: *"Tôi muốn Engine hỗ trợ scalable nhiều context/screen, vì Engine đó sẽ là core engine
trong sự nghiệp của tôi, tôi sẽ tái sử dụng cực nhiều."* ("I want the Engine to scale to many
contexts and screens, because that Engine will be the core engine of my career; I will reuse it
enormously.") The Engine's `ui-architecture.md` §1: *"Runtime — Engine owns: Shell, regions,
navigation, screen lifecycle"*; `EPIC-001D` (backlog) has planned exactly this since 2026-08-23. No
parallel build on the application side. Every new Engine API becomes one line in
`engine_capabilities.py` (`BOT-133`). The detailed split: HLD §5.

### D11 — Enforcement: three AST guards; the allowlist **may only shrink** 🔵 Proposed

`test_module_boundaries.py`, `test_module_domain_is_qt_free.py`, `test_module_declarations.py`,
written with `ast` (the `BOT-133` lesson: a regex matched the API's own documentation). The
violations as found are recorded in Phase 0; each phase shrinks the list; the test fails if it grows.

### D12 — Migration constraint: pure refactoring, no change in business behaviour ✅ Established

Inherited from `EPIC-024C` §4: *"modularize là đổi ranh giới code, không đổi logic nghiệp vụ"*
("modularising changes code boundaries, not business logic"). Coordinators remain owned by their
Presenter and injected through the constructor — never DI-discovered (`async-ui-action-rule.md` §2).

---

## 3. Still open — and what each blocks

| # | Question | Blocks | Answered in |
| :-: | :--- | :-: | :--- |
| ❓ O1 | The **final** list of contribution-point kinds and the schema of each | Phase 0 (`IContributionRegistry`) | Round 2 — HLD §4 is a draft |
| ❓ O2 | The concrete Engine API for `NavigationService` and regions (`EPIC-001D`) | Phase 5 | Round 2 — the Engine-side task |
| ❓ O3 | Per-module QML (D6) | nothing | Phase 4/5 |

---

## 4. Consequences

- `binance_bot_module.py` shrinks to a **module list** in `shell/` — no longer a god file.
- `presentation/ui/common/` **disappears** in Phase 4: the 9 items used only by trading and
  dashboard go to `modules/trading` / `modules/strategy`; the 5 genuinely shared items go to
  `support/ui_kit` or the kernel.
- `EPIC-016`'s `ScreenRegistry` / `AbstractScreenModule` **stay unchanged** until Phase 5 — modules
  contribute screens through exactly that mechanism.

---

## 5. Addendum 2026-09-12/13 — build-or-buy survey (HLD §7) 🟢 User decision

The user asked whether anything we plan to build already exists; HLD §7 records the survey, with
`tach` and `import-linter` run against the real tree. The user's decision (2026-09-13): *"keep the
plan the same, not substitute with lib"*. Consequences:

- D11 stays as written — hand-written `ast` guards. The twelve violations the trial run found are
  the Phase 0 allowlist. `TASK-043` item 4 (the Engine's generalised `import_boundary`) stays.
- Everything surveyed is reference only: PySide6-QtAds (regions), ccxt (a second venue),
  nautilus_trader (the backtest-equals-live reference), finplot (charting), lato and pluggy
  (module patterns). None is a dependency of this epic.
- The one small Engine addition without a dependency, `ScheduledJob.cancel()`, is noted on
  `TASK-043`.

---

## 6. Round-2 decisions, 2026-09-13 🟢 User decision

These answer the three questions HLD §4.2 and §4.5 had left open. Each is a change in
**user-visible behaviour** and is therefore recorded as the user's decision, verbatim.

### D13 — A Welcome (launch) screen is the first screen; it is owned by the shell

Verbatim: *"thêm 1 module màn hình login đơn giản, hiện tên app đẹp đẹp, có cái nút 'login' hay
start... gì đó là được. tôi muốn 1 màn hình giữ chân á mà."* ("add a simple login-screen module:
show the app name nicely, with a 'login' or 'start' button or the like. I want a screen that
greets and holds the user.")

- A new surface `shell/surfaces/welcome/`: the app name and version, the environment banner
  (venue), one primary action **Start**, and the dev-mode switch of D14. It is the **default
  route**; Start navigates to Trading. Dev Board is no longer the default (it was
  `is_default = True`).
- By the workbench rule (HLD §4.6) this is a **shell surface, not a bounded-context module**: it
  is about the application itself, like Settings; it owns no business language and no data.
- The primary action is named **Start**, not "Login", until there is something to authenticate
  (`domain-truth-rule.md`: the UI promises only what the engine delivers — there are no user
  accounts today; exchange credentials live in `secrets.local.json`). The surface is designed so
  that a real login (profile selection, credential unlock) can replace the button later without
  moving anything else: the button dispatches a single `StartRequested` intent that the shell
  handles.

### D14 — Dev Board is hidden unless `dev.mode`; the Welcome screen has the switch; a restart applies it

Verbatim: *"Dev Board ẩn khi dev mode, màn hình login có nút để switch dev mode, có thể cần
restart để enable load module."* ("Dev Board is hidden by dev mode; the login screen has a button
to switch dev mode; a restart may be needed to enable loading the module.")

- The `dev_board` surface and every `dev_probe` are registered **only when `dev.mode` is true at
  boot** (today `dev.mode` gates nothing on Dev Board — measured in HLD §4.2).
- The Welcome screen shows a **Developer mode** toggle. Toggling writes `dev.mode` to the writable
  `user_config.json` (the app's existing config mechanism, `BUG-117` follow-up) and shows "takes
  effect after restart" with a **Restart now** button. Restart relaunches the same executable and
  arguments (`QProcess.startDetached` + quit) — the standard desktop pattern; no hot-loading of
  modules (ADR "deliberately out of scope": no hot reload).
- `--dev` on the command line keeps working and still wins over the file for that run.

### D15 — No manual-order card on Trading; the design keeps the door open

Verbatim: *"không có nhé, nhưng phải thiết kế cân nhắc lỡ sau này có thể mở rộng."* ("no — but
the design must allow extending it later.")

- The manual-order card stays a `trading`-owned widget contributed to `dev_board.rail` only.
- Extension later is **one line** in `modules/trading/module.py::contribute()` — adding
  `trading.rail` as a second place — because of §4.6 rule 2 (one widget, many places). To keep
  that true, the card depends only on `trading`'s own ports (`IOrderSubmission`, `ITradingSession`)
  and never on anything Dev-Board-specific; a test constructs it outside Dev Board.

### D16 — The Engine track is a harvest: build lift-ready in the app, lift on a written criterion 🔵 Proposed

Raised by the user on 2026-09-13 (*"plan sao tui chưa thấy nói tới sẽ làm gì với engine nhỉ?"* —
"why does the plan not say what will be done with the Engine?"). HLD §8 answers it:

- The mechanism (`BoundedContextModule`, the contribution registry, the surface runtime,
  navigation) is built inside the app under `core/contracts/` and `shell/workbench/` with **no
  application import** and the Engine's package layout, then **lifted** into
  `sagittarius_engine/extensions/workbench/` — Fowler's *Harvested Framework*, the pattern the
  Engine's own `EPIC-001D` argues for when it warns against choosing abstractions early.
- **Lift criterion** (all three): zero app imports (guard); used by ≥ 2 surfaces or ≥ 2 modules of
  this app; API unchanged for one whole phase.
- Engine schedule E0–E3 aligned with app phases (HLD §8.4): E0 `ScheduledJob.cancel()` now; E1
  after Phase 1 (module base + registry + descriptors); E2 after Phase 2 (region host, per-place
  models); E3 at Phase 5 (`NavigationService`, screen lifecycle, conformance suite).
- Supersedes HLD §5.3's "until a second application needs it": the second *surface* of this
  application is the evidence.

The SDD for Phase 0 ([`Docs/SDD/`](../../../Docs/SDD/README.md)) fixes the descriptor shape (one
`ContributionDescriptor` for every place, `ScreenContribution` as the sole exception) and the
registry validation rules — this closes ❓ O1 pending the user's review.
