# EPIC-024C — Modularize Market Connector / Market Order / Strategy Engine

> ## ❌ CANCELLED 2026-09-11 — absorbed into [`EPIC-025`](../../EPIC-025_module_theo_bounded_context/README.md) (`PRO-004`)
>
> This task was right in its diagnosis (§2: *"there is no notion of a 'module' for services behind
> the UI anywhere in the app"*) but **wrong in its scope**. The evidence that `EPIC-024B` produced
> (the trigger condition in §1) shows a problem larger than the three pieces Market Connector /
> Market Order / Strategy Engine:
>
> - `BUG-117`: nobody owns the positions read model — a problem of the **whole** Trading context;
> - `BUG-112`: Trading depends on Strategy's state — a problem of the **boundary between two contexts**;
> - 59 method names duplicated between `screens/trading` and `screens/dashboard` — a problem of the
>   **UI layer**, which 024C never touched.
>
> Doing 024C on its own would build the module mechanism **once** for services and then let
> `EPIC-025` build it a **second** time for the whole app — exactly the duplicated mechanism that
> `ONBOARDING.md` §12.5.1 (*"always choose the general solution"*) forbids. The "copy
> `AbstractScreenModule`" template in §2 is **no longer used** either: a business module stands on the
> Engine's `IExtension` (`EPIC-025` ADR D2), not on a third home-made ABC.
>
> **What keeps its value, carried over:** the three questions in §3 are answered in `EPIC-024B` §6
> and became input for HLD §3 (the `modules/trading` contracts). The constraint in §4 (*"change
> code boundaries, not business logic"*) became ADR D12 of `EPIC-025`.
>
> This is not "dropped because it was hard" — the scope was **widened** into its own epic, not narrowed.


- **Trạng thái:** ❌ Cancelled 2026-09-11 — absorbed into `EPIC-025` (see the banner above)
- **Repo:** Elite
- **Chặn bởi:** `B` phải merge xong trước — không bắt đầu chi tiết hoá file này trước đó.

## ⚠️ Đây là khung, không phải task sẵn sàng làm

`PRO-003` §4/§5 chốt rõ: phạm vi của task này **cố ý chưa quyết định** tại thời điểm tạo epic, để
tránh thiết kế ranh giới module khi chưa có consumer thật kiểm chứng. File này chỉ ghi lại những gì
ĐÃ BIẾT chắc từ khảo sát (`PRO-003` §2), không phải kế hoạch thực thi.

## 1. Điều kiện kích hoạt

Ngay khi `EPIC-024B` merge — không phải "khi có thời gian". Người bắt đầu task này phải:
1. Đọc lại `EPIC-024B`'s task file đã hoàn thành (mục "Kết quả xây dựng" nó sẽ có, theo đúng khuôn
   `EPIC-023A-D` đã dùng cả epic trước) — đặc biệt phần nào của `ITradingClient`/
   `ITradingAccountReader` B thực sự cần mà hiện chưa có port thống nhất.
2. Chốt phạm vi C dựa trên đúng nhu cầu đó — không dựa trên phỏng đoán ở file này.

## 2. Những gì đã biết chắc (từ `PRO-003` §2, không đổi bất kể B tìm ra gì thêm)

- `ExchangeSessionFactory` có 2 hàm (`create_trading_client`, `create_futures_metadata_client`) trả
  thẳng SDK Binance thô, không qua port — cần 1 port mới bọc chúng (tên gợi ý:
  `ITradingSessionFactory`) trước khi `EPIC-024A` có thể đổi 3 handler sang dùng port thay vì class
  cụ thể.
- Không có khái niệm "module" cho service phía sau UI trong toàn bộ app — `BinanceBotModule` (656
  dòng) là nơi đăng ký DUY NHẤT cho mọi thứ (data, exchange, strategy, trading session). Nếu
  modularize, mẫu để chép là `AbstractScreenModule` (`src/presentation/ui/registry/
  abstract_screen_module.py`) — app đã có tiền lệ đúng hình dạng này cho màn hình, chỉ chưa có bản
  tương đương cho service.

## 3. Những câu hỏi để B trả lời trước khi chốt phạm vi (không tự đoán)

- B có thực sự cần đọc balance/số dư, hay chỉ cần vị thế (`get_positions()`) là đủ? Nếu cần cả hai,
  đó là bằng chứng cho 1 port "account snapshot" thống nhất (`PRO-003` §2's khoảng trống đã nêu).
- B có tự dựng thêm 1 Coordinator riêng cho form thủ công không (giống
  `StrategyArmingCoordinator`)? Nếu có, đó có thể là hình mẫu tự nhiên cho ranh giới "Market Order
  module" — dùng lại thay vì thiết kế mới.
- 3 handler sau khi `EPIC-024A` sửa xong có thực sự cần 1 module `MarketConnectorModule` riêng, hay
  chỉ cần 1 port bổ sung là đủ (không cần bọc thành class "module" tường minh)? Câu trả lời phụ
  thuộc việc `EPIC-024A` xong có sinh ra bug/nhầm lẫn gì không — chưa có bằng chứng thì chưa cần
  module hoá thêm.

## 4. Không được làm ở đây

- Không dựng `MarketConnectorModule`/`MarketOrderModule`/`StrategyModule` như một bài tập trừu
  tượng trước khi có 3 câu trả lời ở §3.
- Không đổi hành vi của đường chiến lược tự động đang chạy — modularize là đổi ranh giới code, không
  đổi logic nghiệp vụ.
