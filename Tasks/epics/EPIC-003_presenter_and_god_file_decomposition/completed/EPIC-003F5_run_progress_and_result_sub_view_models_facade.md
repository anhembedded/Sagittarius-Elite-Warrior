# EPIC-003F5 — Lát cắt 5 của `003F`: `RunProgressViewModel` + `RunResultViewModel` + facade

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Task cha:** [`EPIC-003F`](../incomplete/EPIC-003F_backtest_viewmodel_composite_design_review.md)
**Trạng thái:** ✅ Xong 2026-09-07
**Rủi ro:** 🟡

---

## 1. Lệch khỏi kế hoạch, có lý do: **1 nhóm → 2 lớp**

`003F1` §7 gọi đây là một nhóm ("tiến trình & kết quả", ~91 dòng). Đọc code thì đó là **hai** câu
hỏi khác nhau:

- *Việc đang chạy tới đâu* — 2 thanh tiến trình (backtest, đồng bộ) có thể chạy **đồng thời**.
- *Lần chạy vừa rồi ra sao* — dòng kết quả, thẻ số liệu, cảnh báo, giới hạn, và tình trạng dữ liệu.

Gộp chúng vào một lớp sẽ tạo ra đúng cái tên mà `architecture-rule.md` §5 cấm: một lớp tên ghép
"…Status" gánh hai trách nhiệm. Nên: `RunProgressViewModel` và `RunResultViewModel`, một task.

## 2. Ba quyết định về ranh giới

1. **`needsDataSync` + `dataCoverageMessage` nằm ở `RunResultViewModel`**, dù trông như cấu hình.
   Cả hai được ghi **từ kết quả** một lần chạy ("không có dữ liệu lịch sử"), và
   `backtest_top_panel.py:696` đọc chúng trong **một biểu thức**:
   `bool(vm.needsDataSync) and vm.dataCoverageMessage != ""`. Hai chủ sở hữu cho hai nửa của một
   banner là cách banner cũ đi một nửa.
2. **`showExtendedMetrics` ở lại facade.** Nó là công tắc hiển thị của người dùng, không thuộc kết
   quả — phải **sống sót** qua lần chạy kế tiếp. Có test riêng cho đúng điều đó.
3. **Một signal cho mỗi thanh, không phải mỗi trường.** `percent` và `text` luôn đổi cùng nhau;
   hai emit cho một lần cập nhật là cách một thanh vẽ % của lần chạy này dưới caption của lần
   trước.

## 3. Kết quả

| File | Việc |
| :--- | :--- |
| `.../view_models/run_progress_view_model.py` | **Mới** — 2 signal / 4 property / 4 slot |
| `.../view_models/run_result_view_model.py` | **Mới** — 6 signal / 9 property / 6 slot + `extended_metrics_snapshot()` |
| `.../backtest_view_model.py` | 1.379 → **1.351 dòng** |
| `tests/.../view_models/test_run_progress_view_model.py` | **Mới** — 4 test |
| `tests/.../view_models/test_run_result_view_model.py` | **Mới** — 6 test |
| `tests/.../test_backtest_view_model_run_status_facade.py` | **Mới** — 5 test forwarding |

**`tests/` diff rỗng tuyệt đối.**

### 3.1 Mutation-verify đã làm thật

Thêm tạm `self.resultChanged.emit()` cạnh delegate trong `set_result` →
`test_each_facade_signal_fires_exactly_once_per_change` đỏ → revert.

## 4. Nhóm cuối (`003F1` §7 gọi là "UI lặt vặt") — kết luận: **không tách**

Còn lại trên facade sau 5 lát: `symbolOptions`/`selectedSymbol`, `initialCapitalText` +
2 thuộc tính validate, `marketRule*`, `selectedCurrency`, `selectedTimeframe`, `executionMode`,
`isChartPreview`, `showExtendedMetrics`, `activeBottomTab`, `scriptModel`, `logModel`,
`isConfigDirty`/`configDiffSummary`/`lastRunSummary`, và khối 10 signal "mở modal".

`003F1` §7 đã nói trước rằng nhóm này **có thể** kết luận là không tách, và đó là kết luận: chúng
không liên quan nhau, nên đứng riêng ở facade là đúng chỗ, không phải việc còn dở. Tách tiếp chỉ
để hạ số dòng sẽ tạo ra các lớp một-thuộc-tính không ai đọc.

**Việc còn lại thật sự của `003F` là bước cuối cùng đã ghi ở §4.3 của nó: gỡ facade** — chỉ mở khi
344 điểm đọc đã dời hết sang sub-VM. Chưa mở.
