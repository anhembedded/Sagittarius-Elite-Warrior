# BOT-127 — Băng console cao theo nội dung, không theo hằng số của Qt

**Trạng thái:** ✅ Hoàn thành (2026-09-08)
**Nguồn:** user báo màn Giao dịch *"mọi thứ quá chen chúc"*, kèm ảnh app thật. Đây là nguyên nhân thứ hai trong ba, giữa [`BOT-129`](BOT-129_moi_man_hinh_cuon_thay_vi_bi_bop.md) (cuộn dọc) và [`BOT-128`](BOT-128_bang_cuon_ngang_thay_vi_mat_cot.md) (cuộn ngang cho bảng).
**Rủi ro:** 🟢 — một `sizeHint` trong `kit/surfaces/log_panel.py`, ảnh hưởng mọi màn có console.

> ⚠️ **File này được viết bổ sung ngày 2026-09-08, SAU khi code đã merge (PR #171).** Đó là một lỗi
> quy trình, không phải lựa chọn: `ONBOARDING.md` §3 nói rõ task file có trước, rồi mới tới code. Ba
> lỗi UI đi liền nhau trong một phiên, và mã `BOT-127` đã bị viết vào docstring + tên test trước khi
> ai kiểm xem file có tồn tại không — tạo ra một tham chiếu **treo** trong `src/` suốt hai PR. Chỉ lộ
> ra khi user hỏi thẳng "3 task đó đã được làm chưa". Ghi lại ở đây thay vì lặng lẽ tạo file cho khớp.

---

## 1. Vấn đề, đo được

Trong ảnh user gửi, băng "NHẬT KÝ GIAO DỊCH" chiếm ~350px và **gần như trống** (3 dòng log), trong
khi vùng làm việc phía trên bị dồn: chart nén còn ~200px, 2 bảng dẹp lét.

Đo trên app thật (boot thật, offscreen, 1920×1080):

| Màn | Băng console | `sizeHint` | Vùng làm việc |
| :--- | ---: | ---: | ---: |
| trading | **244** | 244 | 653 |
| data_management | **244** | 244 | 692 |
| dashboard | **244** | 244 | 697 |

Ba màn, ba lượng log khác nhau, **cùng một con số 244**.

## 2. Root cause

`PageShell` xếp băng console với stretch 0 (`outer.addWidget(self._console_container)`), nghĩa là
băng nhận đúng `sizeHint` của nó. `sizeHint` đó đến từ **mặc định của `QListView` trong Qt** — một
hằng số (~256×192) **không liên quan gì tới model**. Không phải quyết định thiết kế của ai cả, và
không đổi theo số dòng log.

## 3. Sửa

`LogPanel` dùng một `QListView` con hỏi đúng `số dòng × chiều cao dòng`, kẹp giữa:

- **sàn 2 dòng** — console trống vẫn phải đọc ra là một panel có tiêu đề, không phải một sợi chỉ;
- **trần 8 dòng** — quá đó thì người ta cuộn chứ không đọc cả băng, và vùng làm việc không nên mất
  thêm chỗ.

Cả hai là hằng số **đặt tên**, không phải chiều cao băng hard-code: chiều cao thật vẫn do nội dung
quyết định trong khoảng đó.

**Ca list rỗng phải xử riêng, và đó mới là ca quan trọng nhất.** Không có dòng nào thì
`sizeHintForRow(0)` trả `-1`; nếu rơi về hằng số của Qt ở nhánh đó thì defect còn nguyên vẹn — vì
console **rỗng** chính là cái đang giữ chỗ mà không có gì để hiện. Nhánh này lấy chiều cao dòng từ
font metrics của chính view.

## 4. Kiểm chứng

| Màn | Console | Vùng làm việc |
| :--- | :--- | :--- |
| trading | 244 → **134** | 653 → **763** |
| data_management | 244 → **190** | 692 → **746** |
| dashboard | 244 → **160** | 697 → **781** |

**4 test** (`tests/unit/presentation/ui/kit/surfaces/test_log_panel_height.py`), tất cả viết theo
**số dòng** chứ không theo con số pixel — một test assert `== 134` thì chính là cái chiều cao
hard-code cũ, chỉ đổi chỗ. Chúng khoá: quan hệ (rỗng xin ít hơn đầy), độ tăng theo số dòng, cái
trần, và cái sàn.

Cổng `ci-local.ps1 -Full` xanh: `FAILED_STEPS: none`, 3739 passed, coverage 94.78%, grep `LOG_FILE`
0 dòng lỗi. Merge qua PR #171.

## 5. Implementation Notes

**Guard của repo bắt bản nháp đầu.** Class helper ban đầu đặt tên `_ContentHeightListView`, và
`tests/unit/presentation/ui/test_screen_layer_structure.py` chặn: tên class kết thúc bằng `View`
phải nằm trong `screens/*_view.py` vì đó là chỗ dành cho View của bộ MVP. Đổi tên thành
`_ContentHeightLogList` — nó là một widget danh sách, không phải một màn hình — chứ **không** nới
guard cho tiện.
