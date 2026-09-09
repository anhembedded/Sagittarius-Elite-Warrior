# EPIC-024B — Giao dịch thủ công trên Dev Board

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** — (không phụ thuộc A) · **Chặn:** `C` (modularize chốt phạm vi dựa trên kết quả task
  này)

**Rủi ro cao — hành động ảnh hưởng thật tới tài khoản testnet, giống mức rủi ro `EPIC-023D`.** Soát
kỹ trước khi merge.

**Task này là bước chứng minh, không phải hệ quả của một điều đã chứng minh** (`PRO-003`'s lưu ý
2026-09-09): `ExecuteOrderCommandHandler`/`TradingLimitPolicy` được viết cho đúng 1 caller (chiến
lược) từ trước tới giờ. Đây là lần đầu một caller thứ hai (con người, qua form) đi qua chúng — nếu
mọi thứ chạy đúng không cần sửa gì, đó là bằng chứng cơ chế đã tổng quát; nếu lộ ra chỗ phải sửa
(giả định ngầm chỉ đúng khi caller là chiến lược), ghi lại — đó chính là input cho `EPIC-024C`.

**⚠️ Ràng buộc môi trường đã xác minh (2026-09-09) — đọc trước khi coi "chứng minh" ở trên là đã
xong bằng test:** Có bằng chứng thật một lệnh testnet đã khớp trước đây (`EPIC-021G` §5 — order id
`SEW-a91f4c72e0b8`, FILLED thật), nhưng đó là bằng chứng từ một phiên/máy khác. Đã kiểm tra trực
tiếp môi trường hiện tại (session này, 2026-09-09):
- Mạng ra ngoài **tới được** Binance Futures Testnet thật (`ping` endpoint trả `HTTP 200`).
- Nhưng `src/config/secrets.local.json` hiện tại có `API_KEY`/`API_SECRET` **rỗng** — không có
  credentials thật. `tests/testnet/conftest.py`'s `testnet_credentials` fixture sẽ `skip` ngay
  (thiếu credentials), không chạy được, dù có set `SEW_TESTNET_TESTS=1`.

**Hệ quả cho việc "chứng minh" của epic này:** test integration ở §5 (dispatcher thật, trong tiến
trình) chứng minh được **cơ chế nội bộ** (handler/policy/tracker) hoạt động đúng cho caller thứ hai
— chạy được ngay trong môi trường này, không cần credentials thật. Nhưng nó **không** chứng minh
lệnh thật sự khớp trên sàn — đó là việc của tier `tests/testnet/` (opt-in), và tier đó **chỉ chạy
được ở nơi có credentials Futures Testnet thật** (máy của user, hoặc môi trường được cấp
`secrets.local.json` thật). Ghi rõ 2 mức bằng chứng này ra để không nhầm "test integration xanh"
với "đã chứng minh khớp lệnh thật" — 2 việc khác nhau.

## 1. Việc cần làm

Thêm card "Đặt lệnh thủ công" vào Dev Board, mô phỏng form đặt lệnh sàn thật (user cung cấp ảnh
chụp Binance làm tham chiếu): chọn Long/Short, quantity, loại lệnh (Market/Limit), giá (nếu Limit)
— nút submit dispatch **đúng** `ExecuteOrderCommand`/`ExecuteOrderCommandHandler` mà
`LiveTradingCoordinator` (đường chiến lược) đang dùng — không viết lại logic gọi sàn. Kèm khả năng
huỷ MỘT lệnh chờ đang mở (xem §0 dưới đây — hiện chưa tồn tại ở đâu trong app).

**⚠️ Đã loại khỏi phạm vi: ô chọn đòn bẩy/margin mode.** Rà soát 2026-09-09 (`PRO-003` §8.1) xác
nhận `ITradingClient` không có cách nào đổi đòn bẩy/margin mode thật trên sàn — vẽ ô đó trên form sẽ
là UI hiển thị một điều khiển không làm gì cả, vi phạm `domain-truth-rule.md`. Đòn bẩy hiển thị
(read-only, nếu cần) phải lấy từ dữ liệu Binance tự báo lại (`get_positions()`), không phải một ô
người dùng tự chọn. Muốn có ô chọn đòn bẩy thật, cần một port mới (đổi đòn bẩy qua sàn) — đó là việc
của `EPIC-024C` nếu được quyết định cần, không phải việc giả lập ở đây.

## 0. Bổ sung bắt buộc: huỷ 1 lệnh chờ (chưa tồn tại)

Đã kiểm cả `PositionsTable`/`OpenOrdersTable` (Trading + Dev Board) — khả năng huỷ lệnh DUY NHẤT
trong toàn app là `ITradingClient.cancel_all_orders()`, chỉ được gọi từ Dừng khẩn cấp. Không có nút
huỷ trên từng dòng lệnh chờ. `ITradingClient.cancel_order(symbol, client_order_id)` đã tồn tại ở
port — chỉ chưa có ai gọi nó từ UI. Task này phải thêm nút "Huỷ" trên mỗi dòng của
`OpenOrdersPanel`/`OpenOrdersTable` (hoặc tối thiểu trên Dev Board, tuỳ mức UI đã sẵn có lúc code),
dispatch `cancel_order` qua đúng dispatcher — không phải tính năng "có thì tốt", là điều kiện để
"giao dịch thủ công" gọi là đầy đủ (đặt được mà không huỷ được là dở dang).

## 2. Ánh xạ UI → domain (bắt buộc đọc trước khi code)

`domain-truth-rule.md` cấm gộp khái niệm — nút "Long"/"Short" trên UI **không phải** trực tiếp
`OrderSide`. Domain chỉ có `OrderSide.BUY`/`SELL` + cờ `reduce_only`; "Long"/"Short" là *hướng vị
thế*, phụ thuộc vị thế đang có:

| Người dùng bấm | Đang có vị thế | `OrderSide` + `reduce_only` thật |
| :--- | :--- | :--- |
| Long | Không có / đang Long | `BUY`, `reduce_only=False` (mở/tăng Long) |
| Long | Đang Short | `BUY`, `reduce_only=True` (đóng/giảm Short) |
| Short | Không có / đang Short | `SELL`, `reduce_only=False` (mở/tăng Short) |
| Short | Đang Long | `SELL`, `reduce_only=True` (đóng/giảm Long) |

Form phải đọc vị thế hiện tại (qua `ITradingClient.get_positions()`) TRƯỚC khi map — không đoán từ
mỗi symbol/side đơn thuần. Đây là lý do `PRO-003` xếp việc này rủi ro cao, không phải rủi ro thường.

## 3. Thay đổi theo file (dự kiến — điều chỉnh khi code thật cho thấy khác)

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/screens/dashboard/dev_board_panel.py` | Thêm `_build_manual_order_card()`: combo Long/Short (hoặc 2 nút tab), spin quantity, combo loại lệnh, field giá (ẩn khi Market), nút submit. **Không** có ô đòn bẩy/margin (xem cảnh báo §1). Đặt cạnh (không thay thế) card "Chiến lược" — 2 nút Long/Short không phải "Nạp/Gỡ chiến lược". |
| `src/presentation/ui/qml/OpenOrdersTable/` (panel/row liên quan) | Thêm nút "Huỷ" trên mỗi dòng lệnh chờ (§0) — mới, chưa tồn tại. |
| `src/presentation/ui/screens/dashboard/dashboard_view_model.py` | Property/Signal cho form (giống khuôn card Chiến lược của `EPIC-023C`) + `manualOrderRequested` signal mang đủ tham số form + `cancelOrderRequested` signal (symbol, client_order_id) cho nút Huỷ. |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | Handler `_on_manual_order_requested`: đọc vị thế hiện tại qua `ITradingClient.get_positions()`, map theo bảng §2, build `PreviewOrderQuery`, dispatch `ExecuteOrderCommand` — **cùng lời gọi** `LiveTradingCoordinator` dùng, không tự viết logic gọi sàn mới. Handler `_on_cancel_order_requested`: dispatch `ITradingClient.cancel_order()` qua cùng dispatcher. Cả hai chạy qua `ActionOwnershipTracker` riêng (`async-ui-action-rule.md` §2), submit qua `IThreadManager` (không block UI thread). |

## 4. Quyết định thiết kế

- **Không tạo command/use-case mới cho "đặt lệnh thủ công".** `ExecuteOrderCommand` đã là đúng
  contract cần — chỉ cần 1 nơi build `PreviewOrderQuery` từ input người dùng thay vì từ `Signal` của
  chiến lược. Tạo command riêng sẽ là chính "đường đi thứ hai" mà toàn bộ epic này tồn tại để tránh.
- **Không cần port "account snapshot" thống nhất ngay** (`PRO-003` §4) — gọi `ITradingClient.
  get_positions()` trực tiếp để biết hướng vị thế hiện tại là đủ cho task này. Nếu thấy cần đọc
  balance/số dư nữa trong lúc code, đó chính là bằng chứng cho `C` — ghi lại, không tự thêm port
  mới ở đây.
- **Không bỏ qua 3 lớp an toàn** (`EPIC-022` §4.1: venue Testnet, `TradingSessionState.enabled`,
  kết nối) hay 4 giới hạn `TradingLimitPolicy` — chúng áp dụng tự động qua `ExecuteOrderCommandHandler`,
  không cần replicate ở UI, nhưng UI phải hiển thị đúng lý do khi bị chặn (đọc `block_reason` từ kết
  quả, giống cách `EPIC-023D`'s `_BLOCK_REASON_MESSAGES` đã làm cho Enable Trading).

## 4.1. Câu hỏi bắt buộc trả lời trước khi coi task này Done (`PRO-003` §8.2 — không phải giả định)

1. **Đồng thời (concurrency) — ĐÃ TRẢ LỜI (2026-09-09).** Đây là lần đầu `ExecuteOrderCommand` có 2
   nơi gọi thật (tick chiến lược + click tay). Đọc code thật `ExecuteOrderCommandHandler.execute()`
   xác nhận: **có race thật**, không phải giả định — `orders_sent_this_session` được đọc, đánh giá
   4 giới hạn, gửi lệnh thật (network call), rồi mới tăng số lên, và **không có lock nào giữ suốt
   chuỗi đó** — 2 dispatch đồng thời có thể cùng đọc số cũ, cùng qua được `MAX_ORDERS_PER_SESSION`,
   cùng gửi lệnh thật. Xác nhận bằng test dựng race thật (2 thread, `threading.Barrier`, mock sàn có
   delay để mở rộng cửa sổ race) — test đó FAIL trên code cũ (2 lệnh thay vì 1 khi
   `max_orders_per_session=1`), PASS sau khi sửa (mutation-verify đúng `testing-rule.md` §2). **Sửa:**
   thêm `TradingSessionState.live_submission_guard()` — lock thứ hai, tách biệt lock nội bộ hiện có
   (lock đó không được giữ qua network call vì sẽ chặn mọi reader khác như UI polling) —
   `ExecuteOrderCommandHandler` giữ lock này suốt cả chuỗi evaluate→submit→record. Xem chi tiết ở
   commit "EPIC-024B §4.1.1" và docstring của `TradingSessionState`/`live_submission_guard()`.
2. **Con người can thiệp vào symbol chiến lược đang giữ vị thế — ĐÃ QUYẾT (2026-09-09, user chọn).**
   Đọc code thật `signal_action_to_order_intent.py` xác nhận rủi ro là thật, không phải giả thuyết:
   `order_intent_for()` là bảng ánh xạ TĨNH `SignalAction` → `(side, reduce_only)` — chiến lược tự
   nhớ nó đang Long/Short/Flat theo lịch sử signal của chính nó, **không** đọc lại vị thế thật từ
   sàn mỗi tick (khác với form thủ công ở `§2`, buộc phải đọc `get_positions()` trước khi map).
   Nếu người dùng tay đóng vị thế chiến lược đang giữ, lần chiến lược gửi tiếp lệch hướng thật
   (thường chỉ bị sàn từ chối — không nguy hiểm); nhưng nếu người dùng tay MỞ vị thế trên symbol
   chiến lược tưởng đang Flat, lần chiến lược gửi tiếp `reduce_only=False` sẽ **cộng thêm** vào vị
   thế người dùng vừa mở — vượt khỏi quyết định của chiến lược, đúng rủi ro "mất dấu vị thế" mục này
   cảnh báo. **Quyết định:** chặn cứng — nút Long/Short trên form thủ công bị disable (kèm lý do
   hiển thị) khi symbol nhập trùng symbol chiến lược đang `armed` (`LiveStrategySession.is_armed`
   + symbol khớp) **và** đang có vị thế mở trên đúng symbol đó (đọc `ITradingClient.get_positions()`
   — cùng lời gọi §2 đã dùng, không thêm lời gọi mạng mới). Symbol khác (chiến lược không đụng tới)
   vẫn tự do hoàn toàn. An toàn nhất cho lần đầu chứng minh cơ chế — không cần "tự chịu rủi ro" nào
   thêm.

Cả 2 câu hỏi trên đã có câu trả lời — điều kiện merge của mục này đã đủ.

## 5. Kiểm thử

- Unit: map bảng §2 (4 tổ hợp Long/Short × vị thế hiện tại) là bộ test bắt buộc đầu tiên — thuần,
  không cần Qt.
- Unit: `_on_manual_order_requested` dispatch đúng `ExecuteOrderCommand` với `PreviewOrderQuery`
  đúng tham số — mock dispatcher, assert `call_args` giống khuôn `test_dashboard_presenter.py`'s
  các test Enable/Disable đã có (`EPIC-023D`).
- Integration: 1 test end-to-end trong tiến trình (không mock dispatcher, có mock đúng ranh giới
  sàn) tương tự `test_dev_board_known_gaps.py::test_strategy_dropdown_arms_the_selected_strategy` —
  bấm nút Long/Short thật, xuyên qua dispatcher thật/handler thật, xác nhận
  `TradingSessionState`/vị thế cập nhật đúng. Đây là loại test đã bắt được 2 bug thật ở `EPIC-023C`
  — bắt buộc cho task rủi ro cao này. **Chứng minh cơ chế nội bộ, không chứng minh khớp lệnh trên
  sàn thật** — xem cảnh báo môi trường ở đầu file.
- **Testnet tier (opt-in, chỉ chạy được nơi có credentials thật — xem cảnh báo đầu file):** một lệnh
  MARKET khối lượng tối thiểu qua form thủ công, khớp thật, rồi đóng lại — cùng khuôn
  `EPIC-021G` §4 đã làm cho đường chiến lược. Đây mới là bằng chứng "khớp lệnh thật" cho caller thứ
  hai; không có bước này thì "chứng minh" của epic vẫn dừng ở mức cơ chế nội bộ, chưa tới sàn thật.
- Unit: `_on_cancel_order_requested` dispatch đúng `cancel_order(symbol, client_order_id)` — mock
  dispatcher, xác nhận đúng lệnh (không phải lệnh khác) bị huỷ.
- Unit/Integration: test đồng thời cho câu hỏi §4.1.1 — 2 dispatch `ExecuteOrderCommand` từ 2 thread
  khác nhau trong cùng 1 phiên, xác nhận `orders_sent_this_session` không vượt giới hạn dù chạy song
  song.
- Xác minh bằng mắt: `SEW_CAPTURE_SCREENSHOTS=...` cho card mới (kèm nút Huỷ trên Open Orders), đúng
  quy trình `EPIC-023A` đã đặt.
