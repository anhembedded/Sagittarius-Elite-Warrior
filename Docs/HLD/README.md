# HLD — High-Level Design chính thức của Sagittarius Elite Warrior

- **Trạng thái:** 🟢 Vòng 1 duyệt 2026-09-11 (ADR: [`EPIC-025/DECISION_2026-09-11_module_boundaries.md`](../../Tasks/epics/EPIC-025_module_theo_bounded_context/DECISION_2026-09-11_module_boundaries.md)).
  Vòng 2 còn mở: schema contribution point (§4, ❓ O1) và API Engine cụ thể (§5, ❓ O2).
- **Vai trò:** đây là **kim chỉ nam** — tài liệu duy nhất trả lời *"module nào, ranh giới ở đâu, theo
  tiêu chí gì, API ra sao"*. Task/epic/bug **tham chiếu** tới đây, không chép lại. Khi code và HLD
  lệch nhau, một trong hai **sai** và phải sửa ngay trong PR đó — không để lệch qua sprint.
- **Nguồn gốc:** [`PRO-004`](../../Tasks/proposal/PRO-004.md) (đề xuất + bằng chứng đo được) →
  ADR (quyết định) → HLD này (thiết kế). Sơ đồ: [`as_is.puml`](../../Tasks/proposal/PRO-004_assets/as_is.puml)
  / [`to_be.puml`](../../Tasks/proposal/PRO-004_assets/to_be.puml).
- **Ngôn ngữ:** tiếng Việt (như `Docs/PROJECT_INTENT_AND_USER_STORIES.md`); định danh code tiếng Anh.

## Khung tư duy: 5 câu hỏi → 5 công cụ

User đặt bài toán bằng 3 câu; khảo sát cho thấy phải là 5, mỗi câu có đúng một công cụ đã có tên
và tiền lệ lớn — **không phát minh khái niệm mới**:

| # | Câu hỏi | Công cụ | Nguồn | Trả lời ở |
| :-: | :--- | :--- | :--- | :--- |
| 1 | **Cắt ở đâu?** | Bounded Context + Aggregate làm tiêu chí cắt; Distillation (Core/Supporting/Generic) | DDD chiến lược (Evans) | [§1](01_tieu_chi_cat_module.md), [§2](02_context_map.md) |
| 2 | **Các mảnh nói chuyện với nhau thế nào?** | Context Map: Customer/Supplier, Open Host Service + Published Language, Anticorruption Layer | DDD chiến lược | [§2](02_context_map.md), [§3](03_hop_dong_module.md) |
| 3 | **Bên trong mỗi mảnh tổ chức sao?** | Clean Architecture (domain / application / adapters / ui), Port = ABC | Robert Martin | [§3](03_hop_dong_module.md) |
| 4 | **Lắp vào app không biết trước số mảnh?** | Microkernel + DIP: `IExtension` của Engine, Martin's "Main" = `shell/`, contribution point kiểu VS Code | Microkernel, VS Code extension model | [§3.1](03_hop_dong_module.md), [§4](04_surface_va_contribution_point.md), [§5](05_engine_app_split.md) |
| 5 | **Làm sao để nó không mục sau 3 sprint, và đi tới đó mà app vẫn chạy?** | Architecture fitness function (guard AST, allowlist chỉ co); Strangler Fig + Walking Skeleton | Ford/Parsons/Kua; Fowler | [§6](06_enforcement_va_di_tru.md) |

## Mục lục

1. [Tiêu chí cắt module (C1–C6) và áp dụng lên app này](01_tieu_chi_cat_module.md)
2. [Context map: 4 bounded context, 4 support, kernel; Distillation; kiểu tích hợp; Published Language](02_context_map.md)
3. [Hợp đồng module: `BoundedContextModule`, bố cục bên trong, contracts từng module, bảng ánh xạ code hôm nay](03_hop_dong_module.md)
4. [Surface và contribution point: Trading, Dev Board (`dev_probe`), Settings, CLI](04_surface_va_contribution_point.md)
5. [Engine nhận mechanism, app giữ policy: bảng chia với `EPIC-001D`](05_engine_app_split.md)
6. [Enforcement và di trú: 3 guard, allowlist ratchet, 6 phase](06_enforcement_va_di_tru.md)

## Quy ước đọc

| Nhãn | Ý nghĩa |
| :--- | :--- |
| ✅ | Đã có trên cây code hôm nay (trích `file:line`), thiết kế **tái dùng** |
| 🔵 | Thiết kế mới, chưa implement |
| ❓ | Còn mở — chặn phase ghi kèm |
| ⚠️ | Điểm dễ làm sai, đã có tiền lệ trả giá trong repo |
