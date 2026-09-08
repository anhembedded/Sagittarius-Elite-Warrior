# BOT-128 — Bảng cuộn ngang thay vì mất cột

**Trạng thái:** ✅ Hoàn thành (2026-09-08)
**Nguồn:** user báo màn Giao dịch chật chội, kèm ảnh app thật; sau khi sửa `BOT-129` (cuộn dọc) và `BOT-127` (băng console) thì lỗi này còn lại.
**Rủi ro:** 🟠 — sửa `DataTable.qml`, component dùng chung của **6 bảng**.

---

## 1. Triệu chứng, đo được

Trong ảnh user gửi: bảng Vị thế chỉ hiện 3/7 cột, bảng Lệnh chờ 4/7. Tiêu đề cột bị cắt **giữa
chữ** — "KHỐI LU", "CHI", "KIỂU L". Không có thanh cuộn nào để kéo tới phần còn lại.

Đo trên app thật (boot thật, offscreen, cửa sổ 1920×1080):

| Bảng | Cột khai (tổng) | Bề rộng được cấp | Thiếu |
| :--- | ---: | ---: | ---: |
| Vị thế | 110+70+120+130+130+70+130 = **760** | ~391 | **369** |
| Lệnh chờ | 150+110+70+130+120+130 = **710** | ~390 | **320** |

`trading_view.py:422-423` đặt 2 bảng **cạnh nhau**, mỗi bảng nhận nửa vùng chính.

## 2. Root cause

Header cell của `DataTable.qml` mang `Layout.minimumWidth: 0` (thêm từ `BUG-076`, để cột
`fillWidth` co được mà không tràn chữ). Hệ quả không lường trước: **mọi** cột đều co được xuống 0,
nên `RowLayout` bóp những cột nó bóp được và **đẩy phần còn lại ra khỏi mép**.

Tệ hơn một tầng: bề rộng cột là **Single Source of Truth dùng chung với row delegate** của caller —
header co nhưng row **không** co, nên hai bên lệch nhau. Đúng cái mà quy ước SSOT sinh ra để chặn.

## 3. Sửa — hướng general, không phải vá tại chỗ

User chốt (2026-09-08): *"luôn chọn general solution"*. Ghi thành luật ở
[`ONBOARDING.md`](../../.agents/ONBOARDING.md) §12.5.1.

Hai hướng đã cân:

| | Hướng | Được | Mất |
| :-: | :--- | :--- | :--- |
| A | Xếp 2 bảng chồng dọc trong `trading_view.py` | 1 dòng, hết đau ngay | 5 bảng còn lại vẫn dính đúng lỗi đó |
| **B** ✅ | `DataTable.qml` tự cuộn ngang | **Cả 6 bảng** hết mất cột, ở mọi bề rộng cửa sổ | Đụng component dùng chung, cần đo lại |

Chọn **B**. Agent ban đầu đề xuất A vì rẻ hơn; user bác, và đúng — A để nguyên lỗi ở 5 chỗ khác.

**Cơ chế:** `DataTable` cộng bề rộng cột đã khai (`requiredWidth`), bọc header + divider + rows
trong một `Flickable` có `contentWidth: Math.max(width, requiredWidth)`, kèm `ScrollBar` ngang chỉ
xuất hiện khi thật sự có chỗ để kéo tới. Header cell đổi `Layout.minimumWidth` từ `0` thành đúng
bề rộng đã khai — cột **không co nữa, bảng cuộn**. Cột `fillWidth` (không khai bề rộng) vẫn giữ
`minimumWidth: 0` + `elide` như `BUG-076` yêu cầu.

Bảng nào vừa khung thì `contentWidth == width` → **không đổi gì so với trước**.

## 4. Kiểm chứng

**Đo lại trên app thật sau khi sửa:**

| Bảng | Host | `contentWidth` | Thanh cuộn |
| :--- | ---: | ---: | :--- |
| Vị thế | 391 | **896** | `visible=True`, hiện 43.6% |
| Lệnh chờ | 390 | **838** | `visible=True`, hiện 46.5% |

**5 test** (`tests/unit/presentation/ui/qml/test_data_table_horizontal_scroll.py`) nạp thẳng
`DataTable.qml` ở bề rộng hẹp hơn cột của chính nó — điều kiện mà không test màn hình nào tái hiện:
khung hẹp thì cuộn được; `contentWidth` phủ **đủ** mọi cột đã khai (không phải chỉ "rộng hơn khung",
vì rộng thiếu vẫn giấu cột, chỉ khác là có thanh cuộn đứng trước); khung rộng thì **y như cũ**;
thanh cuộn báo đúng tỉ lệ nhìn thấy; và cột khai bề rộng **không bị bóp**.

Hai điều chỉnh trong lúc viết test, ghi lại vì cả hai đều là test-sai-cách:
- Test đầu không giữ tham chiếu widget → Qt xoá object C++ → `RuntimeError` thay vì fail đúng giá trị.
- Assert trên `policy` của `ScrollBar` **không đọc được** từ Python (`Can't find converter for
  'QQuickScrollBar::Policy'`). Đổi sang `size` (tỉ lệ nhìn thấy) — một test không đọc nổi giá trị nó
  khẳng định thì không phải test.

Cổng `ci-local.ps1 -Full` xanh, có grep `LOG_FILE`.

## 5. Luật đã cập nhật

- [`ONBOARDING.md`](../../.agents/ONBOARDING.md) §12.5.1 — nguyên tắc "luôn chọn general solution",
  kèm chính ca này làm ví dụ, và ranh giới của nó (phạm vi chứ không phải chi phí: general phải là
  dạng tổng quát của **đúng vấn đề đã báo**, không phải trừu tượng hoá đầu cơ).
- [`ui-presentation-rule.md`](../../.agents/rules/ui-presentation-rule.md) — bảng hẹp hơn cột của nó
  thì **cuộn**, không bao giờ bỏ cột; `DataTable` sở hữu việc này cho mọi bảng, đừng giải lại theo
  từng màn.


---

## 6. Implementation Notes (2026-09-08)

**Hai test sai trước khi đúng**, ghi lại vì cả hai đều là kiểu sai làm test vô giá trị:

1. Test đầu **không giữ tham chiếu widget** → Qt xoá object C++ → `RuntimeError: Internal C++ object
   already deleted` thay vì fail đúng giá trị. Một test nổ vì lý do khác thì không đo được gì.
2. Assert trên `ScrollBar.policy` — **không đọc được** từ Python
   (`Can't find converter for 'QQuickScrollBar::Policy'`), nên nó ném thay vì so sánh. Đổi sang
   `size` (tỉ lệ nội dung đang nhìn thấy). Một test không đọc nổi giá trị nó khẳng định thì không
   phải test.

**Verify:** cổng `-Full` xanh (`FAILED_STEPS: none`, 3756 passed, coverage 94.91%, `LOG_FILE` sạch),
cộng đo trên app thật: bảng Vị thế khung 391px / `contentWidth` 896px, Lệnh chờ 390/838, thanh cuộn
`visible=True`. Merge qua PR #173.
