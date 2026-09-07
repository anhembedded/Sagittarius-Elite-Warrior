# EPIC-003B2 — `DataManagementPresenter` → `logic/ui_mode_transitions.py`

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Nối tiếp:** [`EPIC-003B`](EPIC-003B_data_management_coordinator_pilot.md)
**Trạng thái:** ✅ Xong 2026-09-07 · **Rủi ro:** 🟢

---

## 1. Đối tượng

12 lời gọi `fsm.add_transition(...)` nằm giữa `__init__` (162 dòng), xen giữa việc dựng coordinator
và gắn log handler. Chúng **không phải wiring** — chúng là một **bảng**: tập nước đi hợp lệ của FSM
màn này. Muốn trả lời "màn này có đi từ `CANCELLING` sang `ERROR` được không" phải cuộn qua một
`__init__` 162 dòng và tự gộp 3 nhóm phân cách bằng comment.

## 2. Kết quả

| File | Việc |
| :--- | :--- |
| `.../data_management/logic/ui_mode_transitions.py` | **Mới** — `ALLOWED_TRANSITIONS` (14 cặp) + `install_transitions(fsm)` |
| `.../data_management_presenter.py` | 874 → **857 dòng**; `__init__` 162 → 144 |
| `tests/.../data_management/logic/test_ui_mode_transitions.py` | **Mới** — 6 test |

**`tests/` diff rỗng tuyệt đối.**

## 3. Test nói đúng cái code làm, không nói cái mình mong

`test_clearing_has_no_cancel_path` ghim **thực tế**: `CLEARING` không có đường huỷ. Bản comment đầu
tôi viết là "cố ý vắng mặt vì DB xoá dở không quay lại được — xem `_on_clear_database`" — **sai hai
lần**: không có hàm tên đó, và "cố ý" là suy diễn của tôi chứ không có chỗ nào chép lại. Đã sửa
thành điều kiểm chứng được bằng code: `_on_cancel` chỉ chuyển trạng thái khi đang ở
`SYNCING`/`SCANNING`, và 3 handler xoá/purge (`_on_clear_data`, `_on_clear_row`, `_on_purge_all`)
không đưa cancellation token nào cho worker. Thêm một hàng `(CLEARING, CANCELLING)` mà không có phần
plumbing đó sẽ quảng cáo một nút Huỷ mà màn hình không thực hiện được.
