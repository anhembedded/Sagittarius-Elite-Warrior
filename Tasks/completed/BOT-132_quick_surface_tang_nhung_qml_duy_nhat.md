# BOT-132 — `QuickSurface`: một tầng nhúng QML duy nhất thay cho 10 host tự dựng `QQuickWidget`

**Trạng thái:** ✅ Hoàn thành (2026-09-10)
**Nguồn:** [`BUG-115`](../bug_report/completed/BUG-115_qquickwidget_transparent_clear_colour_black_or_see_through_on_hardware_compositor.md)
§4 — thiết kế đã được user duyệt 2026-09-10 ("ok duyệt, làm app trước, Engine làm luôn").
**Rủi ro:** 🟠 — đụng cả 10 host QML sản xuất + 11 `preview.py`; đổi cách mọi modal/bảng QML được
dựng. Không đổi contract công khai nào (setter/signal/`root_object` giữ nguyên tên).
**Độ phức tạp:** 🔴 `L (Thinking Agent)` — cầu nối QtWidgets ↔ QML, hai đường render của Qt.

---

## 1. Vấn đề — tóm tắt từ `BUG-115`

Cả 10 host `QQuickWidget` trong app lặp lại 12 dòng giống nhau, kèm `setClearColor(transparent)`
với comment *"để nền SURFACE của cha lộ ra"*. Giả định đó chỉ đúng trên đường vẽ phần mềm
(`offscreen`, `widget.grab()` — tức toàn bộ tầng test). Trên màn hình thật Qt đục lỗ backing store
dưới `QQuickWidget` và ghép texture lên nền clear **đen** (X11) / **xuyên thấu** (Wayland). Mọi thân
modal QML và bảng QML hiển thị sai trên Ubuntu; `BUG-102` chỉ sửa được phần chrome.

Nguyên nhân thiết kế (không phải một dòng sai): cầu nối QtWidgets ↔ QML là **quy ước copy-paste**,
không phải abstraction; Engine đã có `create_quick_widget()` nhưng app bỏ qua ở 17 chỗ vì
`configure_app_qml()` bị gỡ khỏi bootstrap từ `EPIC-006F` và không được khôi phục khi `EPIC-015`
đưa QML trở lại.

## 2. Thiết kế (đã duyệt — chi tiết và hình PlantUML ở `BUG-115` §4.3, `BUG-115_assets/design_*.puml`)

| Tầng | Việc | Ai |
| :--- | :--- | :--- |
| Engine (`TASK-042`, repo riêng) | `create_quick_widget(background_token="bg")` — clear colour **đục**, đọc từ token; từ chối token không đục | `runtime/quick_background.py` |
| App `kit/style.py` | `background_token(role)` + `_STATIC_BACKGROUND_TOKENS` — **nguồn duy nhất**: `_build_qss()` cũng đọc bảng này (qua `_background()`), nên nền QSS của cha và clear colour của scene không thể lệch | `kit/style.py` |
| App `qml/embed/` | `QuickSurface(qml_file, surface: StyleRole, context, size_policy)` — nơi **duy nhất** tạo `QQuickWidget` (qua factory Engine); giữ context sống; nạp-hoặc-raise; `root_object`; `QuickSizePolicy.FILL/HUG` | `quick_surface.py`, `size_policy.py` |
| Bootstrap | `seed_app_theme()` — **một** hàm mồi theme cho mọi tiến trình dựng widget (bootstrapper + 6 script đứng ngoài nó) | `theme_bootstrap.py` |
| Guard | cấm `QQuickWidget()`/`(QQuickWidget)`/`setClearColor(` ngoài `qml/embed/` | `test_quick_widget_only_in_embed.py` |
| Hợp đồng | clear colour đục == token của role; role không có nền tĩnh bị từ chối lúc dựng; HUG/FILL | `tests/unit/presentation/ui/qml/embed/test_quick_surface.py` |
| Desktop tier | so pixel màn hình thật ↔ `grab()` trong vùng QML trống (`xvfb-run` trên Linux) | `scripts/quick_surface_desktop_probe.py` |

Bất biến mới (ghi vào `qml-rule.md` §0): **một scene QML nhúng luôn đục, nền là token của
`StyleRole` nó được nhúng vào — đúng luật child `QWidget` trên `QFrame`.**

## 3. Các bước — mỗi bước xanh gate trước khi sang bước sau

| Bước | Việc | Trạng thái |
| :--- | :--- | :---: |
| S1 | bootstrap + `embed/` + `background_token` + 3 guard/hợp đồng/probe | ✅ |
| S2 | `QmlOverlay` (kéo theo 10 dialog) | ✅ |
| S3 | 5 host compose: `SymbolPickerModal`, `MetricsDetailModal`, `DatabaseStatusPanel`, `PositionsPanel`, `OpenOrdersPanel` | ✅ |
| S4 | 4 host kế thừa: `ProgressBannerWidget`, `StatusPillWidget`, `StatCardRowWidget`, `ChartToolbar` (`HUG`) | ✅ |
| S5 | 11 `preview.py`; xoá `qml/style.py` (bản chép `ensure_qml_style` của Engine); guard xanh | ✅ |
| S6 | `qml-rule.md`; phụ lục `BUG-102`; đóng `BUG-115`; ROADMAP; gate `-Full`; đo lại Xvfb | ✅ |

## 4. Kiểm thử

- Trước khi migrate (S1): guard `test_no_qquickwidget_is_built_or_subclassed_outside_embed` **đỏ đúng
  lý do** ở mọi host/preview cũ; `test_no_host_sets_a_clear_colour` đỏ ở 10 host.
- `scripts/quick_surface_desktop_probe.py` dưới `xvfb-run`/xcb: `screen=#111318 grab=#111318` —
  cùng thí nghiệm mà `BUG-115_assets/quickwidget_transparency_probe.py` (cơ chế cũ) cho
  `screen=#000000`.
- Sau S2: chạy lại `modal.py` (TimeframePicker thật) trên Xvfb — 3 điểm mẫu §1 của `BUG-115`.
- Sau S6: `pwsh scripts/ci-local.ps1 -Full` → `LOG_FILE` grep `FAILED|ERROR|Traceback|ResourceWarning`;
  chạy lại `shoot.py` xcb: pixel-diff Data Management về ~0 %.


---

## 5. Implementation Notes (viết khi xong — `ONBOARDING.md` §3.4)

### 5.1 Lỗi thật gặp trong lúc làm

1. **Bandit `B105` chặn tên hằng bên Engine.** `DEFAULT_BACKGROUND_TOKEN = "bg"` bị gate của Engine
   báo *"Possible hardcoded password"* — heuristic của bandit bắt chữ `token` trong tên. Đổi thành
   `DEFAULT_BACKGROUND` và tham số `background`. Ghi lại vì cái tên "…_TOKEN" là phản xạ tự nhiên
   cho một API đọc design token, và sẽ đỏ lần nữa nếu ai đó đặt lại.
2. **Không được gán attribute trước `super().__init__()` của `QWidget`.** `ChartToolbar` xây
   `TimeframeVM` *trước* khi gọi `super()` (vì `QuickSurface` nhận context lúc dựng), nên
   `self._pin_preferences`/`self._active` phải thành biến cục bộ rồi gán lại sau `super()`.
   `get_current` dùng `getattr(self, "_active", active_code)` cho đúng khoảng thời gian ngắn đó.
3. **`QuickSurface` là một `QWidget` trần → đụng guard `find_bare_qt_base_widgets`.** Đúng, và đây
   là ngoại lệ thật: nó **không vẽ gì** (scene tự clear, nền QtWidgets là của `Panel`/`Overlay`
   quanh nó). Gắn `# base-exempt: a transparent holder, not a surface` kèm lý do, đúng quy ước
   `kit/guards.py` — không nới trần.
4. **Test click phải nhắm vào `QQuickWidget` bên trong, không phải host.** Toạ độ từ
   `item.mapToScene()` nằm trong không gian của Quick window; khi host thành `QuickSurface`
   (compose), `QTest.mouseClick(host, ...)` lệch. Thêm property công khai `quick_widget` và sửa 6
   chỗ test. Đây là cái giá có thật của việc đổi từ kế thừa sang compose, nêu rõ thay vì giấu.
5. **Preview nạp bằng đường dẫn nên không có package cha** — mọi `preview.py` phải import tuyệt đối
   (`Sagittarius_Elite_Warrior.src...`), không được `from ..embed import`. `preview_qml.py` đã ghi
   điều này trong docstring; bản nháp đầu vẫn dính.
6. **Gate bắt 2 lỗi thật mà tầng unit không bắt được — cả hai đều do tôi, và đều đáng sửa tận gốc.**
   (a) 4 test `test_shutdown_*_process.py` chạy `scripts/shutdown_*_probe.py` như **tiến trình
   thật** và đỏ với `RuntimeError: create_quick_widget() called before configure_app_qml()`: hai
   probe đó dựng UI **không** qua `app_bootstrapper.build()` và chỉ gọi `get_theme_bridge(...)`,
   thiếu `configure_app_qml()`. Trước `BOT-132` thiếu vẫn "chạy được" vì mỗi host tự set `Theme`;
   sau khi mọi scene đi qua factory Engine thì thiếu là lỗi cứng.
   **Không vá 2 chỗ:** rà ra **6** entry point mỗi cái giữ một bản chép riêng của việc mồi theme
   (2 probe chỉ gọi bridge, 3 script chỉ gọi `configure_app_qml`, `preview_qml.py` gọi cả hai +
   pin style). Gom thành **một** hàm `src/presentation/ui/theme_bootstrap.py::seed_app_theme()`;
   bootstrapper và cả 6 script gọi nó. Đây đúng lớp lỗi mà `BOT-132` sinh ra để đóng, gặp lại ở
   một trục khác (mồi theme thay vì nhúng scene).
   (b) 3 test integration click thẳng vào host (`QTest.mouseClick(toolbar, ...)`) — đổi từ kế thừa
   sang compose làm toạ độ lệch. Sửa sang `.quick_widget`, cùng lý do đã ghi ở mục 4.
7. **Bảng `_STATIC_BACKGROUND_TOKENS` ban đầu vẫn là bản chép thứ hai** của những gì `_build_qss()`
   viết literal — đúng thứ hồ sơ này nói là muốn xoá. Đảo phụ thuộc: `_build_qss()` đọc bảng qua
   `_background(role)`, nên bảng là nguồn duy nhất; thêm test lặp mọi role trong bảng và assert QSS
   thật chứa đúng giá trị token đó (`test_style.py`). Tự soát ra khi đọc lại diff, không phải do
   test đỏ — ghi lại vì nó là lỗi "sửa đúng hướng nhưng chưa tới nơi".
8. **Thư mục clone Engine đặt ở `/home/user/sagittarius_engine` che mất chính package** khi
   `PYTHONPATH=/home/user` (namespace package rỗng thắng bản cài editable) — 9 test collection error
   không liên quan gì tới code. Chỉ là môi trường sandbox, nhưng đúng lớp bẫy `ONBOARDING.md` §12.6
   dặn A/B trước khi kết luận.

### 5.2 Quyết định thiết kế đáng nhớ

- **Vì sao `QuickSurface` compose `QQuickWidget` thay vì kế thừa:** kế thừa thì mọi host lại có
  toàn bộ API `QQuickWidget` trong tay, kể cả `setClearColor` — đúng thứ vừa gây ra bug. Compose
  + guard làm cho việc lặp lại lỗi này *không gõ được*, chứ không chỉ "bị khuyên đừng".
- **Vì sao token nền là `StyleRole`, không phải chuỗi:** chuỗi là bản sao thứ hai của sự thật
  "host này ngồi trên nền gì"; `StyleRole` đọc từ chính bảng `apply_role()` vẽ, nên hai hoạ sĩ
  không thể lệch. Role không có nền tĩnh (hover/selected/gradient/transparent) thì raise ngay lúc
  dựng.
- **Vì sao Engine chỉ biết "đục", app biết "token nào":** `StyleRole` là vocabulary của app;
  `ui-architecture.md` §4 của Engine cấm runtime biết app. Ranh giới này giữ `TASK-042` tái dùng
  được cho consumer khác.

### 5.3 Số đo cuối

- **Gate bắt buộc `pwsh scripts/ci-local.ps1 -Full` (2026-09-10): `RESULT: PASS`, `FAILED_STEPS: none`.**
  Ruff Lint ✅, Ruff Format ✅, Mypy ✅, Skill Prompt References ✅, Tests ✅, Sanity ✅, Run-log scan ✅.
  **3894 passed, 4 skipped, 0 failed**; coverage **94.73 %** (ngưỡng 80 %). Đọc thẳng `LOG_FILE`
  (17.859 dòng) theo `CLAUDE.md` mục 2 — grep `FAILED|ERROR|Traceback|ResourceWarning` chỉ còn 4
  dòng, và cả 4 đều **không** phải lỗi: 2 dòng là tên tham số của một test (`[ERROR]` — chính test
  `StatusPill` ở chế độ ERROR, PASSED), 2 dòng còn lại là tiêu đề + kết quả của bước "Run Log Scan".
  Ba lượt gate trước đó đỏ và đã sửa thật, ghi ở §5.1 mục 6 (không phải flake).
- Gate Engine (`pwsh scripts/ci-local.ps1`): Lint/Format/Mypy/Bandit/Pip-Audit/Architecture ✅;
  Tests 1416 passed, 1 failed = `test_agents_docs_resolve.py` — **fail y hệt khi stash thay đổi
  đi**, không thuộc task này (A/B theo `ONBOARDING.md` §12.6).
- Màn hình thật (Xvfb/xcb): pixel-diff `grab()` ↔ màn hình **0,00 %** trên Backtest, Data
  Management và Giao dịch; 3 điểm mẫu của `BUG-115` §1 từ `#000000` → `#111318`.
