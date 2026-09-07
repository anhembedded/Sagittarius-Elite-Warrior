# EPIC-003F6 — Gỡ facade `BackTestViewModel` (bước cuối của `EPIC-003F`)

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Task cha:** [`EPIC-003F`](EPIC-003F_backtest_viewmodel_composite_design_review.md) §4.3
**Trạng thái:** 🟡 Đang làm — Phase 0 và Phase 1 xong 2026-09-07, 5 phase còn lại chưa mở
**Rủi ro:** 🔴 — task duy nhất của `EPIC-003F` **bắt buộc phải sửa test**, ngược hẳn hợp đồng của `003F1`…`F5`

---

## 1. Đây là task duy nhất được phép sửa test — và vì sao điều đó nguy hiểm

Bảy lát cắt trước (`003F1`…`F5`, `003E2`/`E3`/`G2`/`B2`) đều lấy **`git diff --name-only tests/`
rỗng** làm bằng chứng facade đúng. Task này thì ngược lại: gỡ facade **là** đổi API, nên mọi call
site phải đổi theo, kể cả 355 chỗ trong `tests/`.

Đó chính là chỗ nguy hiểm. Sửa hàng loạt dòng test trong lúc "chỉ đổi tên" là kiểu sửa dễ làm test
xanh vì lý do sai nhất trong repo này — đã xảy ra 2 lần trong phiên 2026-09-07 (mock container trả
`Mock()` khiến 7 test Settings đi nhánh khoá; và một assert `save_count == 1` đo nhầm đối tượng).

**Luật cho task này:** mỗi phase chỉ được đổi **đường dẫn thuộc tính**, bằng phép thay thế có quy
tắc (regex có neo receiver), **không** đổi một giá trị assert nào. Diff của `tests/` phải đọc được
100% là `x.foo` → `x.<nhóm>.foo`. Bất kỳ dòng test nào phải sửa **nội dung** là tín hiệu dừng lại
và hỏi, không phải sửa cho xanh.

## 2. Đo lại thật, thay con số đã trôi

`EPIC-003F` §2 ghi **344 điểm đọc** — đo 2026-08-27, trước khi 5 sub-VM ra đời. Đo lại 2026-09-07
(khớp `<receiver>.<member>` với receiver là biến ViewModel thật, loại màn Trading vốn trùng tên
thuộc tính, loại luôn file định nghĩa sub-VM và test của chính sub-VM):

| Nhóm | `src` | file | `tests` | file | Tổng |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `run_progress` | 14 | 2 | 19 | 4 | **33** |
| `strategy_params` | 28 | 7 | 48 | 5 | **76** |
| `trade_log` | 28 | 4 | 56 | 7 | **84** |
| `time_range` | 32 | 8 | 52 | 9 | **84** |
| `broker_sim` | 12 | 2 | 86 | 5 | **98** |
| `run_result` | 55 | 8 | 94 | 7 | **149** |
| **Tổng** | **169** | | **355** | | **524** |

Không phải 344. Con số cũ **không** sai lúc nó được đo — nó chỉ đã trôi 11 ngày và 5 lát cắt.

## 3. Kế hoạch: 1 phase nền + 6 phase theo nhóm

### Phase 0 — mở đường (✅ xong 2026-09-07, thuần thêm mới)

6 sub-VM đang là thuộc tính private (`_run_progress`…). Không thể dời call site sang một thứ nó
không gọi tên được. Phase 0 thêm 6 accessor công khai — `trade_log`, `strategy_params`,
`time_range`, `broker_sim`, `run_progress`, `run_result` — **không đổi một call site nào**, 198
test màn Backtest xanh y nguyên.

`@property` Python trần, không `Property(QObject, constant=True)`: `EPIC-006` đã xoá sạch `.qml`,
không gì marshal chúng sang QML nữa. Chỉ đọc, không setter: sub-VM dựng một lần trong `__init__`,
gán lại một cái sẽ để mọi signal còn nối vào instance cũ.

### Phase 1 — `run_progress` (✅ xong 2026-09-07)

Nhóm nhỏ nhất, chọn làm mẫu để nhìn thấy hình dạng diff trước khi làm 5 nhóm còn lại. 25 chỗ đổi
bằng regex, 0 assert đổi. Xoá 4 property + 4 slot + 2 signal khỏi facade.

Một việc **không** thuần đổi tên, đã làm tay và ghi lại: `test_backtest_view_model_run_status_facade.py`
gác cả 2 nhóm; nửa progress của nó không còn facade nào để chứng minh nên đã xoá, phần
`run_result` giữ nguyên. Hành vi của `RunProgressViewModel` vẫn được
`view_models/test_run_progress_view_model.py` phủ đầy đủ — không mất độ phủ, chỉ mất một lớp gác
cho thứ không còn tồn tại.

### Phase 2…6 — chưa mở

Thứ tự đề nghị, rủi ro tăng dần: `strategy_params` (76) → `trade_log` (84) → `time_range` (84) →
`broker_sim` (98) → `run_result` (149).

Mỗi phase là một commit riêng, mỗi commit phải qua `ci-local.ps1 -Full` xanh có grep `LOG_FILE`.

## 4. Một chỗ chặn thật, phải xử trước `time_range` và `broker_sim`

`state_persistence.py` đọc/ghi bằng `getattr(view_model, field.prop)` / `setattr(...)` với
`field.prop` là **tên phẳng** (`"commissionText"`, `"timeRangePreset"`, `"displayTimezone"`…) khai
trong `backtest_state_fields.py`. Gỡ facade là 24 dòng bảng đó trỏ vào hư không —
`getattr` sẽ ném `AttributeError` lúc khôi phục phiên, **không phải** lúc import, nên `mypy` và
mọi test không chạm state persistence đều im lặng.

Cách xử (chưa làm): cho `StateField.prop` nhận đường dẫn có dấu chấm
(`"broker_sim.commissionText"`) và cho `state_persistence` đi theo đường đó. `_among()` ở
`backtest_state_fields.py:133` cũng `getattr` một `options_prop` — cùng một sửa.

**Không được** để phase nào đụng `time_range`/`broker_sim` chạy trước khi chỗ này xong.

## 5. Điều kiện dừng

`EPIC-003F` §4.3 đã cho phép sẵn: *"Nếu dừng giữa chừng, facade ở lại; nó vẫn đúng, chỉ là chưa
đẹp."* Phase nào chưa làm thì nhóm đó vẫn đi qua facade — hai lối cùng tồn tại không sao, vì lối
facade chỉ là `return self._<sub>.<x>`.

Task **đóng** khi cả 6 nhóm đã dời và `backtest_view_model.py` không còn thuộc tính chuyển tiếp
nào. Ước tính khi đó: 1.345 → khoảng 250-300 dòng.
