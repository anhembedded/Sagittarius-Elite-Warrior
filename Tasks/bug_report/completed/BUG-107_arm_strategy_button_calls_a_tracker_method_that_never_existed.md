# BUG-107 — Nút "Nạp chiến lược" gọi một method chưa từng tồn tại của `ActionOwnershipTracker`, mọi lần bấm đều `AttributeError`

**Reported date:** 2026-09-07
**Fixed date:** 2026-09-07
**Severity:** 🟠 P1 — tính năng nạp chiến lược live (`EPIC-022D`) **hỏng hoàn toàn**: không có
đường nào khác để arm một chiến lược từ UI, và lỗi ném ra **trước** cả dòng logic đầu tiên nên
không có `ArmStrategyCommand` nào được gửi đi. User thấy một nút bấm không làm gì cả.
**Status:** ✅ Fixed 2026-09-07 (root-caused / reproduced / regression-tested / verified)

---

## 1. Hiện tượng (Symptom)

Log user gửi (phiên thật trên Windows, 2026-09-07 22:31:22) — bấm nút "Nạp chiến lược" ở màn
Giao dịch:

```text
2026-09-07 22:31:22,369 - App - ERROR - Uncaught UI Exception: 'ActionOwnershipTracker' object has no attribute 'start_action'
Traceback (most recent call last):
  File "...\src\presentation\ui\screens\trading\trading_presenter.py", line 653, in _on_arm_requested
    self._arming_coordinator.on_arm_clicked()
  File "...\src\presentation\ui\screens\trading\coordinators\strategy_arming_coordinator.py", line 269, in on_arm_clicked
    action = self._tracker.start_action(self._arm_action_kind, None)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'ActionOwnershipTracker' object has no attribute 'start_action'
```

Phần còn lại của log (live stream, sync, chart, `EmergencyStopCommand` báo thiếu credentials) là
hoạt động **bình thường**, không liên quan. Xem §6 về các dòng `TypeError` QML ở cuối log.

## 2. Nguyên nhân gốc rễ (Root cause)

`ActionOwnershipTracker`
([`src/presentation/ui/common/action_ownership_tracker.py`](../../../src/presentation/ui/common/action_ownership_tracker.py))
**chưa từng có** method tên `start_action`. API thật để mở một action là:

```python
def begin_action(self, kind: TKind, config: TConfig, previous_state: TState) -> ActionContext[...]
```

— ba tham số, và **luôn** trả về một `ActionContext`, không bao giờ `None` (việc "đè" một action
đang chạy do chính `begin_action` xử lý bằng `INVALIDATED`, không phải bằng cách từ chối cái mới).

`strategy_arming_coordinator.py:269` gọi `self._tracker.start_action(kind, None)` — **hai** tham
số, một cái tên không tồn tại — rồi kiểm tra `if action is None: return` như thể đó là một cơ chế
chống double-click. Cả hai đều là giả định sai:

- Tên method sai → `AttributeError` ngay dòng đầu tiên của `on_arm_clicked()`.
- Kể cả nếu tên đúng, `begin_action` không bao giờ trả `None`, nên nhánh `if action is None` là
  code chết. Việc arm ở đây là **đồng bộ** trên UI thread (`self._dispatcher.dispatch(...)` chạy
  thẳng, không qua `IThreadManager`), nên cũng không có action nào đang bay để mà đụng nhau.

Mã lỗi này ra đời ở `9f235c9` (`EPIC-022`, viết thẳng trong `TradingPresenter`) và được **bê
nguyên xi** sang Coordinator ở `4697d4a` (`BOT-125` self-review) — một lần refactor chỉ di chuyển
dòng lệnh chứ không chạy nó.

### 2.1 Vì sao không có cửa nào chặn được nó

Đây là phần đáng ghi lại hơn cả bản thân lỗi — **cả ba lớp bảo vệ đều mù đúng chỗ này**:

1. **mypy**: `[tool.mypy] exclude` trong `pyproject.toml` loại **toàn bộ** `src/presentation/`
   (`EPIC-002A`, 24 file / 133 lỗi, 52% là false positive của `@Property` PySide6). Một lời gọi
   method không tồn tại trên một class có kiểu rõ ràng là đúng loại lỗi mypy bắt được trong một
   nốt nhạc — nhưng file này nằm ngoài vùng nó nhìn.
2. **ruff**: không phân tích liên-module, không biết `ActionOwnershipTracker` có method nào.
3. **Test**: `test_trading_strategy_arming.py` có 12 test, tất cả gọi `arm()`/`disarm()` — hai
   method **nằm dưới** nút bấm. `on_arm_clicked()` (chính là cái nút) và cả chuỗi
   `requestArm()` → `armRequested` → `_on_arm_requested` → `on_arm_clicked()` **không có một
   test nào** (`grep -rn "armRequested\|requestArm" tests/` trả về rỗng). 70/70 test màn Trading
   xanh với bug nằm nguyên trong đó.

## 3. Fix

[`strategy_arming_coordinator.py`](../../../src/presentation/ui/screens/trading/coordinators/strategy_arming_coordinator.py)
`on_arm_clicked()`:

```diff
-        action = self._tracker.start_action(self._arm_action_kind, None)
-        if action is None:
-            return
+        action = self._tracker.begin_action(self._arm_action_kind, None, None)
```

`(kind, None, None)` khớp đúng cách `TradingPresenter` gọi tracker của chính nó cho nút bật/tắt
giao dịch (`self._toggle_tracker.begin_action(_TOGGLE_ACTION, None, None)`) — cùng một tracker
`ActionOwnershipTracker[str, None, None]`, cùng một nghĩa: kind là `str`, không có config và
không có previous_state để khôi phục. Nhánh `if action is None` bị xoá vì nó là code chết, không
phải vì "tiện tay" — lý do được ghi vào docstring của method để lần sau không ai thêm lại.

Kèm theo, đúng một thay đổi nhỏ về hợp đồng: tham số `tracker` của `__init__` được ghi kiểu đầy
đủ `ActionOwnershipTracker[str, None, None]` thay vì generic trần — đúng thứ `TradingPresenter`
truyền vào, và là kiểu khai báo tường minh mà `architecture-rule.md` yêu cầu (generic trần =
`Any` ở cả ba tham số kiểu).

**Không** đổi thiết kế: tracker vẫn do Presenter sở hữu và truyền vào, Coordinator vẫn không tự
sinh action id (`async-ui-action-rule.md` §2).

## 4. Regression test (viết trước, xác nhận đỏ đúng lý do trước khi sửa)

`tests/unit/presentation/ui/screens/trading/test_trading_strategy_arming.py` — **5 test mới**,
tất cả đi qua `on_arm_clicked()` chứ không phải `arm()`:

| Test | Chứng minh điều gì |
| :--- | :--- |
| `test_the_arm_button_dispatches_and_reports_success` | Một cú bấm thật gửi `ArmStrategyCommand` và báo lại cho user |
| `test_the_arm_button_registers_its_action_with_the_presenters_tracker` | **Bằng chứng dương** cơ chế ownership thật sự chạy: tracker của Presenter trả về đúng action, đúng `kind`, outcome `SUCCEEDED` |
| `test_a_refused_arm_leaves_the_action_failed_and_says_why` | Bị từ chối là một action đã **kết thúc** (`FAILED`), không phải `PENDING` treo — một action treo sẽ fence luôn cú bấm kế tiếp |
| `test_an_arm_that_raises_is_reported_and_finishes_its_action` | Nhánh `except` (cũng gọi `finish_action`) |
| `test_the_presenter_wires_the_arm_signal_to_the_button_handler` | Đi trọn đường của nút thật: `requestArm()` → `armRequested` → `_on_arm_requested` → `on_arm_clicked()` trên một `TradingPresenter` thật |

Tracker trong các test này là `ActionOwnershipTracker` **thật**, không phải `Mock` — một `Mock`
chấp nhận mọi tên method và sẽ xanh với đúng bug này trong đó (`bug-fix-rule.md` §3, bài học
`BUG-013`).

**Trước khi sửa: 5/5 đỏ đúng lý do**, cùng `AttributeError` và cùng dòng như log user gửi; riêng
test qua Presenter tái hiện **nguyên văn** traceback của user (`trading_presenter.py` →
`_on_arm_requested` → `strategy_arming_coordinator.py` → `on_arm_clicked`):

```text
5 failed, 70 passed, 1 error
AttributeError: 'ActionOwnershipTracker' object has no attribute 'start_action'
```

**Sau khi sửa: 75/75 xanh** (`tests/unit/presentation/ui/screens/trading/`).

### 4.1 Dọn trùng lặp kèm theo (lý do, không phải tiện tay)

Bốn fixture `mock_config`/`container`/`view`/`presenter` đang được **copy nguyên văn** trong
`test_trading_presenter_toggle.py` và `test_trading_presenter_emergency_stop.py`. Viết test đi
qua Presenter cho nút arm sẽ là **bản copy thứ tư** — nên chúng được dời vào `conftest.py` của
package test đó, đúng lý do và đúng chỗ mà docstring của chính conftest ấy đã ghi khi nó ra đời.
`test_trading_presenter_equity.py` giữ `container` riêng: nó bind thêm `IEventBus` để assert lên
đó — khác biệt thật, không phải bản sao.

## 5. Verification

- `tests/unit/presentation/ui/screens/trading/` — **75/75 xanh** (trước: 70, +5 test mới).
- **Cổng bắt buộc `scripts/ci-local.ps1 -Full` — exit `0`**, chạy trên Linux
  (`pwsh 7.4.6`, venv Python 3.12, engine cài từ GitHub):

  ```text
  ✅ Ruff Check / Ruff Format / Mypy / Skill Prompt References passed
  3751 passed, 4 skipped, 1 warning in 208.08s
  Required test coverage of 80% reached. Total coverage: 94.95%
  ✅ Tests passed   ✅ Sanity passed
  ✅ Run log — no WARNING/ERROR/CRITICAL log records
  FAILED_STEPS: none
  ```

  Đã đọc `LOG_FILE` (`logs/ci-local-latest.log`, 21.641 dòng) và grep
  `FAILED|ERROR|Traceback|ResourceWarning` theo đúng `CLAUDE.md` quy tắc 2 — không có kết quả nào
  ngoài tên các test có tham số `[ERROR]` và chính dòng hướng dẫn của script.

## 6. Những dòng còn lại trong log user gửi — đã kiểm tra, KHÔNG phải bug mới

Cuối log là một loạt `TypeError: Cannot read property 'stateIdleBg'/'accent'/'muted'/... of null`
từ `StatusPill.qml`, `Button.qml`, `ProgressBanner.qml`, `PanelHeader.qml`, `DataTable.qml`,
`TimeframeToolbar.qml`, `TimeRangePicker*.qml`. Tất cả nằm **sau** dòng `App stopped.`:

- Đây là teardown noise **đã được biết và ghi lại**: docstring của
  [`src/presentation/ui/qml/host.py`](../../../src/presentation/ui/qml/host.py) (mục *"A cost this
  host does NOT solve"*) và `.agents/ONBOARDING.md` §5 đều mô tả đúng hiện tượng này — QML binding
  tính lại khi context property (`Theme`, `vm`) bị null-hoá lúc scene bị huỷ.
- Khác với `BUG-069`/`BUG-103` (đọc `vm.x`, đã guard `vm ? vm.x : ...`), lần này object bị null là
  **`Theme`** — thứ mọi dòng màu trong mọi `.qml` đều đọc, nên không guard được bằng cùng cách mà
  không rải `Theme ? ... : ...` khắp toàn bộ file `.qml` của app.
- Không có lỗi nào trong nhóm này xuất hiện **trong lúc app đang chạy** ở log user gửi, và không
  có triệu chứng nhìn thấy được.

Nếu user muốn dọn nốt phần tiếng ồn này, nó là một task riêng (sửa ở tầng host: xoá source /
huỷ context property trước khi tear down, thay vì guard từng file) — cố ý **không** gộp vào commit
sửa lỗi này.

## 7. Bài học rút ra

**Một refactor "chỉ di chuyển code" vẫn phải chạy code đó ít nhất một lần.** `4697d4a` bê nguyên
lời gọi hỏng từ Presenter sang Coordinator; test suite xanh cả trước lẫn sau vì không test nào
chạm tới entry point của nút bấm.

**Test entry point của nút, không phải method nằm dưới nó.** 12 test đã bao phủ rất kỹ `arm()`
nhưng `on_arm_clicked()` — thứ Qt thật sự gọi — thì không. Khoảng trống đó chính xác là chỗ bug đi
lọt ra tới user.
