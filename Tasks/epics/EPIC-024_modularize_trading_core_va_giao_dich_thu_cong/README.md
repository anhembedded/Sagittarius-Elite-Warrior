# EPIC-024 — Giao dịch thủ công trên Dev Board + Modularize Trading Core

- **Trạng thái:** 🔴 Chưa bắt đầu (0/3 task con)
- **Repo:** Elite
- **Nguồn gốc:** [`PRO-003`](../../proposal/PRO-003.md) — đề xuất kiến trúc đã được duyệt thành epic
  này. Đọc `PRO-003` trước khi làm bất kỳ task con nào — epic này chỉ tóm tắt quyết định, không lặp
  lại phần phân tích/bằng chứng.
- **Lập ngày:** 2026-09-09, theo yêu cầu trực tiếp của user: quan sát Trading screen hiện chỉ có
  một nơi gọi cơ chế đặt lệnh (chiến lược tự động), không có cách nào tự tay đặt lệnh Long/Short
  như một sàn thật. **Đúng chiều nhân-quả** (user tự sửa lại): cơ chế đó có tổng quát cho một
  caller thứ hai (con người) hay không là điều **chưa được chứng minh** — việc B chạy qua đúng cơ
  chế đó chính là bước chứng minh, không phải một tính năng thêm vào sau khi đã có bằng chứng.

---

## 1. Quyết định đã chốt (xem `PRO-003` §4 để biết đầy đủ lý do)

**Hai sáng kiến, ràng buộc với nhau — B chưa "Done" cho tới khi C được lên kế hoạch cụ thể:**

1. **(A)** Sửa vi phạm kiến trúc nhỏ đã xác nhận (3 handler dùng thẳng class cụ thể thay vì port)
   — độc lập, làm ngay, không đổi hành vi.
2. **(B)** Giao dịch thủ công trên Dev Board — xây trên port đã có (`ITradingClient`,
   `ITradingAccountReader`), tái dùng đúng `ExecuteOrderCommand`/`ExecuteOrderCommandHandler` mà
   chiến lược đang dùng.
3. **(C)** Modularize Market Connector / Market Order / Strategy Engine — **phạm vi cố ý chưa chốt
   hết**, chốt sau khi (B) xong, dựa trên bằng chứng thật (B) bộc lộ. Không phải "làm sau nếu có
   thời gian" — là điều kiện hoàn thành của (B).

**Không đảo thứ tự B/C:** modularize trước khi có consumer thật (B) là thiết kế đoán mò, rủi ro
phải sửa lại (`PRO-003` §5).

## 2. Mục tiêu

Kết thúc epic, một dev đứng ở Dev Board phải làm được: chọn symbol, tự tay đặt lệnh Long/Short
(quantity, leverage tự chọn) — đi qua đúng cơ chế an toàn (Testnet-only, `TradingSessionState.
enabled`, `TradingLimitPolicy`) mà chiến lược tự động đã có, không phải một đường đi mới; và ranh
giới Market Connector/Market Order/Strategy Engine phải được đặt tên tường minh (mirroring
`AbstractScreenModule`), không còn là các phương thức riêng lẻ gộp trong `BinanceBotModule`.

## 3. Thứ tự thực hiện

| # | Task | Chặn bởi | Trạng thái |
| :-: | :--- | :--- | :---: |
| **A** | [Sửa vi phạm: handler dùng port thay vì class cụ thể](incomplete/EPIC-024A_sua_vi_pham_kien_truc_port.md) | — | 🔴 |
| **B** | [Giao dịch thủ công trên Dev Board](incomplete/EPIC-024B_giao_dich_thu_cong_dev_board.md) | — | 🔴 |
| **C** | [Modularize Market Connector / Market Order / Strategy Engine](incomplete/EPIC-024C_modularize_trading_core.md) | B (phạm vi chốt sau khi B xong) | 🔴 |

## 4. Ngoài phạm vi, cố ý

- Không đổi hành vi của đường tự động (chiến lược) trong (A)/(B) — chỉ thêm một trigger thứ hai
  (con người) vào cùng một cơ chế đã có.
- (C) không được bắt đầu chi tiết hoá trước khi (B) merge — tài liệu (C) hiện tại chỉ là khung, không
  phải task sẵn sàng làm.
