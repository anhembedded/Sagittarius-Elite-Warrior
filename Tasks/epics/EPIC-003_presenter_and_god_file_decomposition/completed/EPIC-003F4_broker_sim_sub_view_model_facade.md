# EPIC-003F4 — Lát cắt 4 của `003F`: `BrokerSimViewModel` + facade

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Task cha:** [`EPIC-003F`](EPIC-003F_backtest_viewmodel_composite_design_review.md)
**Trạng thái:** ✅ Xong 2026-09-07
**Rủi ro:** 🟡 — nhóm lớn nhất trong 5 lát (`003F1` §7 ước 179 dòng), nhưng cùng khuôn.

---

## 1. Phạm vi

Toàn bộ nhóm "tham số broker" (`BOT-104`): 12 `Property`, 12 `Signal`, 10 `Slot` `set_*`.

`orderSizeType/Value/Text` · `pyramiding` · `commissionType/Value/Text` · `slippageTicks` ·
`longLeverage` · `shortLeverage` · `takeProfitPctEnabled` · `takeProfitPctText`.

Đây đúng là tập trường mà `_build_run_config()` đọc để dựng 1 `PositionSizing` + 1
`BrokerSimulationConfig` — trả lời một câu hỏi duy nhất: *lệnh này đáng lẽ tốn bao nhiêu*.

## 2. Hai quyết định thiết kế, không phải chuyển nguyên si

1. **Các mức chặn (clamp) đi theo state, không theo form.** `pyramiding >= 1`,
   `commissionValue >= 0`, `slippageTicks >= 0`, `leverage >= 1` giờ là hằng số có tên
   (`MIN_PYRAMIDING`, …) ngay cạnh setter thực thi chúng. Clamp chỉ nằm trong dialog là clamp mà
   một state file chép tay hoặc một lệnh ghi từ Presenter đi vòng qua được — đúng lỗ hổng
   `LiveStrategyConfig` đã bịt bằng `__post_init__` ở màn Giao dịch.
2. **Mặc định thành hằng số có tên** (`DEFAULT_ORDER_SIZE_TEXT` = `"100"`, …) để test đọc **cùng
   con số** mà code dùng, thay vì chép lại chuỗi vào assert.

Hành vi giữ nguyên tuyệt đối, kể cả chi tiết dễ mất: `_set_order_size_text` vẫn ghi thẳng
`_order_size_value` (bỏ qua clamp) rồi phát **cả hai** signal — hai nơi đọc khác nhau (dialog đọc
`*Text`, run config đọc `*Value`), một emit sẽ để một bên cũ.

## 3. Kết quả

| File | Việc |
| :--- | :--- |
| `.../view_models/broker_sim_view_model.py` | **Mới** — 12 property / 12 signal / 10 slot + 12 hằng số |
| `.../backtest_view_model.py` | 1.405 → **1.379 dòng** |
| `tests/.../view_models/test_broker_sim_view_model.py` | **Mới** — 6 test (trong đó 6 case parametrize riêng cho clamp) |
| `tests/.../test_backtest_view_model_broker_sim_facade.py` | **Mới** — 4 test forwarding |

**`tests/` diff rỗng tuyệt đối.**

### 3.1 Mutation-verify đã làm thật

Thêm tạm `self.pyramidingChanged.emit()` vào **`Slot set_pyramiding` của facade** →
`test_each_facade_signal_fires_exactly_once_per_change` đỏ → revert. Ghi rõ "Slot", không ghi
"`_set_pyramiding`": lần mutate đầu tôi đảo `_set_pyramiding` (setter của `Property`) và test
**không** đỏ, vì test gọi Slot chứ không gán property — chú thích trong test đã sửa lại cho đúng
đường thật.

### 3.2 Một test của chính tôi sai trước, code đúng

`test_a_half_typed_number_keeps_the_text_and_the_last_good_value` ban đầu dùng `"0."` làm ví dụ
"gõ dở" — sai: `float("0.")` = `0.0`, nên phím đó **thật sự** đặt size về 0. Đổi sang ô rỗng
(`float("")` mới ném `ValueError`), và ghi lại nhầm lẫn ngay trong docstring để người sau không
lặp lại.
