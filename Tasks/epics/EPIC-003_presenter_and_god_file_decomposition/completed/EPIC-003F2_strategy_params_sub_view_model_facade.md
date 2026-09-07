# EPIC-003F2 — Lát cắt 2 của `003F`: `StrategyParamsViewModel` + facade

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Cha:** [`EPIC-003F`](EPIC-003F_backtest_viewmodel_composite_design_review.md)
**Trạng thái:** ✅ Hoàn thành (2026-09-07) · **Ngày mở:** 2026-09-07

---

## 1. Vì sao lát cắt này, không phải lát khác

`BackTestViewModel` còn **1.426 dòng / 64 property / 70 signal** sau `003F1`. Đếm thật bằng AST,
gom theo tiền tố tên:

| Nhóm | Thành viên |
| :--- | ---: |
| `botparams` + `strategy` | **17** (6 property, 11 signal) |
| `order` | 7 |
| `symbol` | 6 |
| `capital` | 6 |
| `progress` | 6 |

Chọn nhóm 17 vì cùng một lý do `003F1` chọn trade log: **cohesive nhất**, không phải nhỏ nhất.
Cả 17 phục vụ đúng một việc — chọn chiến lược và sửa **Thông số Chiến lược** — và cùng một luồng
người dùng duy nhất (mở picker → mở dialog thông số → lưu). Không có thành viên nào của nhóm này
bị đọc bởi một luồng khác.

Thêm một lý do đã đo được: `EPIC-022` vừa dựng đúng cấu trúc này cho màn Giao dịch
(`build_bot_params_schema`/`rows`/`parse` đã ở `components/strategy_params/` từ `EPIC-022C`), nên
sub-ViewModel này sẽ là **cùng hình dạng ở cả hai màn** — thứ mà lần sau ai gộp tiếp sẽ cần.

## 2. Ràng buộc — chép từ `003F` §4, không sửa

1. **Facade trước, dời sau.** Chỉ tạo sub-ViewModel và cho `BackTestViewModel` forward sang.
   **Không sửa một call site nào.**
2. **Bằng chứng đúng = `tests/` diff RỖNG TUYỆT ĐỐI.** Nếu phải sửa một dòng test thì facade sai,
   dừng lại. (Đây là bằng chứng `003F1` và `BOT-124` đều đã dùng.)
3. **Không "big bang"** — 17 thành viên, không phải 64.
4. **Gỡ facade là task riêng, cuối cùng** — không làm ở đây.

## 3. Thiết kế — theo đúng `003F1` §3

- `@Property` forward viết tay, **không `__getattr__`**: `presentation/` nằm ngoài cổng `mypy`, nên
  `__getattr__` biến mọi tên viết sai thành hợp lệ tĩnh **và** im lặng lúc chạy. 6 property viết
  tay thì `AttributeError` nổ ngay và `grep` ra được.
- Signal của sub-VM `connect` thẳng tới signal cùng tên trên facade, **không `emit()` thủ công** —
  nhân đôi đường phát đúng là lớp lỗi `BUG-042` đã trả giá.
- `step_bot_param_value()` đi cùng `_bot_params_schema` — nó chỉ đọc schema đó, tách ra là tạo
  hai nguồn sự thật.

### Không làm ở task này

| Không làm | Vì |
| :--- | :--- |
| Dùng chung sub-VM này với màn Giao dịch | Đó là đổi hành vi 2 màn cùng lúc; bước facade phải chứng minh "không đổi gì" |
| Gộp `selectedStrategyName` vào `humanize_strategy_key` | Backtest có `name` thật trong `strategyOptions`, Trading thì không — hai nguồn khác nhau, gộp là mất thông tin |
| Dời 5 nhóm còn lại | Ràng buộc §2.3 |

## 4. Thay đổi theo file

| File | Việc |
| :--- | :--- |
| `screens/backtest/view_models/strategy_params_view_model.py` | **Mới** — 6 property + 11 signal + state, mang theo `step_bot_param_value()` |
| `screens/backtest/backtest_view_model.py` | Dựng sub-VM, forward, nối signal; **xoá** state đã dời |
| — | **Không file nào khác.** Đó là định nghĩa của bước facade |

## 5. Verify

`tests/` diff rỗng + toàn bộ CI gate xanh.


---

## 6. Xong 2026-09-07

**Phạm vi thu hẹp so với §1, có lý do.** §1 đếm 17 thành viên theo tiền tố tên, nhưng khi đọc code
thì `openStrategyPickerRequested`/`openBotParamsRequested` nằm trong khối **10 signal "mở modal"**
của màn hình. Kéo 2 cái ra khỏi khối đó chỉ để khớp tiền tố là **đổi một cohesion lấy một cohesion
tệ hơn**. Tương tự, 3 signal `*SaveRequested`/`*CommitRequested` do `Slot` phía dialog phát ra —
chúng mang **ý định người dùng**, không phải state.

Thực dời: **5 signal state + 6 property + 5 method + `step_bot_param_value()`**.

**Bằng chứng đúng — điều kiện §2.2 đạt:**

```
git diff --name-only tests/   →  (rỗng)
```

`tests/` **không bị sửa một dòng nào**. 919 test màn hình xanh; CI gate đầy đủ **3.639 passed,
4 skipped**, đã grep log thật.

`backtest_view_model.py`: **1.426 → 1.417 dòng.** Con số nhỏ, và đó là điều đúng của bước facade:
state đi chỗ khác nhưng forward ở lại. Giá trị thật nằm ở chỗ `StrategyParamsViewModel` (160 dòng)
giờ là một đơn vị đọc/sửa/test được một mình, và nó có **cùng hình dạng với card Chiến lược của màn
Giao dịch** (`EPIC-022`) — điều kiện cần nếu sau này muốn dùng chung một ViewModel cho cả hai màn.

Rút ngắn thật sự chỉ đến ở task gỡ facade (§2.4), sau khi mọi call site đã dời.
