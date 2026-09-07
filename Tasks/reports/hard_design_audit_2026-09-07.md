# Rà soát hard design & khả năng mở rộng — 2026-09-07

**Yêu cầu:** *"rà soát tất cả, fix hard design, mọi thứ phải sẵn sàng mở rộng, không lặp cơ chế"*
**Phạm vi:** toàn `src/` (635 file), không giới hạn ở diff của phiên này.
**Tiêu chí đo được:** thêm 1 thứ mới phải sửa mấy file, và có gì báo khi quên sửa không.

---

## 1. Kết quả tóm tắt

| # | Phát hiện | Đo được | Trạng thái |
| :-: | :--- | :--- | :--- |
| 1 | **12 bản cùng một cơ chế** "enum → nhãn tiếng Việt", 3 hành vi khác nhau khi thiếu member | 12 file | ✅ Đã gộp về `EnumLabels` + guard |
| 2 | **Lỗi thật do #1**: `EnableTradingBlockReason.SUPERSEDED_BY_CONCURRENT_STATE_CHANGE` không có câu nào | 1 nhánh | ✅ Đã sửa |
| 3 | **26 bản container giả** trong test — thêm 1 dependency = sửa tới 26 file | 26 file | 🟡 Cơ chế chung đã có, mới áp 3 file |
| 4 | 20 file vượt ngưỡng 400 dòng | 20 file | ⬜ `EPIC-003` sở hữu |
| 5 | Feed pattern | 7 Feed / 1 `BaseFeed` | ✅ Không lặp — đã đúng |
| 6 | Đăng ký chiến lược / indicator script | 3 nơi mỗi thứ | ✅ Chấp nhận — xem §4 |

## 2. Phát hiện 1+2 — cơ chế lặp sinh ra lỗi thật

`grep` ra **12** khai báo dạng `dict[SomeEnum, str]` trong `presentation/`. Không phải 12 lựa chọn
phong cách — là **12 cơ hội thêm member enum rồi quên viết câu cho nó**, và chúng phản ứng khác
nhau khi điều đó xảy ra:

| Cách tra | Khi thiếu member | Số nơi |
| :--- | :--- | :-: |
| `.get(member, "câu chung chung")` | user thấy câu vô nghĩa, **không ai biết là thiếu** | 3 |
| `table[member]` | `KeyError` — với CLI formatter nghĩa là traceback thay vì bản báo trạng thái | 1 |
| không tra trực tiếp | bảng buộc phải đúng, không có gì kiểm | 8 |

**Một cơ hội đã bị lấy.** Script kiểm tra đầy đủ (chạy thật, không suy đoán):

```
EnableTradingBlockReason         4/5 ['SUPERSEDED_BY_CONCURRENT_STATE_CHANGE']  <-- THIẾU
```

Đó là nhánh của `BUG-088`: một DỪNG KHẨN CẤP chen vào giữa lúc đang đối soát để bật giao dịch.
Call site dùng `.get(reason, "Không thể bật giao dịch.")` — nên **đúng cái từ chối mà user cần
được giải thích nhất lại hiện câu chung chung nhất.**

### Đã làm

`src/presentation/enum_labels.py` — `EnumLabels(TheEnum, {...})`:

- kiểm **đầy đủ lúc dựng** (tức lúc import): thiếu member ⇒ app không khởi động được, test báo
  ngay lúc collect. Ồn còn hơn muộn, nhất là với câu chữ giải thích vì sao lệnh bị từ chối.
- từ chối luôn nhãn rỗng/toàn khoảng trắng (lọt `in`, rồi hiện thành dòng trống bí ẩn) và key
  thuộc enum khác.
- **cố ý không có `get(default)`** — chính cái default đó đã che lỗ ở trên.

Áp cho cả 12 nơi. Thêm `tests/unit/presentation/test_enum_labels.py`: 5 test cho bản thân cơ chế,
+ **1 guard đi bộ AST toàn `src/presentation/`** bắt bất kỳ ai khai báo lại `dict[SomeEnum, str]`
bằng tay. Hiện: 0 vi phạm.

## 3. Phát hiện 3 — 26 bản container giả

Mỗi file test dựng Presenter đều tự viết một `Mock()` có `resolve` là chuỗi `if interface is X`,
kết thúc bằng `return Mock()`.

**Chi phí đo được:** thêm 1 dependency vào Presenter = sửa tới 26 file. Phiên này dính đúng 2 lần
(`TradingSessionState`, `LiveStrategySession`) — và lần thứ hai **tệ hơn là làm vỡ test**: vì
chuỗi kết thúc bằng `Mock()`, container chưa được dạy trả về `session_state.enabled` là một `Mock`
truthy, nên test vẫn xanh trong khi đang chạy nhầm nhánh.

**Đã làm:** `fake_container()` + fixture `make_container` trong `tests/conftest.py`, khớp theo
identity rồi theo tên class (vài file import `IConfig` từ đường dẫn khác với code — đó là lý do
nhiều chuỗi cũ phải có nhánh `interface.__name__ == "IConfig"`), và **nhớ mock đã tạo** để 2 lần
resolve cùng interface trả về cùng object — chuỗi cũ trả object mới mỗi lần, âm thầm sai với mọi
service dùng chung.

**Chưa làm hết, cố ý:** mới áp cho 3 file test màn Giao dịch (những file phiên này làm mong manh).
Chuyển nốt 23 file còn lại là churn cơ học trên code không thuộc phạm vi lượt review, mỗi file một
chuỗi hơi khác nhau — rủi ro đổi hành vi âm thầm cao hơn giá trị. Cơ chế đã sẵn cho code mới.

## 4. Cái KHÔNG sửa, và vì sao

**Đăng ký chiến lược/indicator script vẫn thủ công** (`binance_bot_module._register_strategies`).
Auto-discovery bằng quét module nghe "sẵn sàng mở rộng" hơn, nhưng với bot giao dịch thì một
chiến lược **vô tình** được đăng ký là rủi ro tiền thật, và danh sách tường minh chính là thứ
review được. Đây là lựa chọn có chủ đích của repo, không phải hard design.

**20 file vượt 400 dòng** — `EPIC-003` ("Phân rã Presenter/File quá tải", 5/8) đã sở hữu. Lượt
này chỉ đưa `trading_presenter.py` từ 926 → 879 bằng cách chuyển đúng lát cắt phiên này thêm vào.
Refactor `backtest_presenter.py` (1966 dòng) trong một lượt review là mở rộng phạm vi quá mức.

## 5. Ghi nhận chưa kết luận

Lần chạy CI thứ 5 hôm nay xuất hiện `Exception ignored in atexit callback` (đệ quy
`AxisItem.boundingRect` trong pyqtgraph, **sau** khi 3638 test đã pass). Không có ở 4 lần trước.
Chạy lại lần 6: **0 lần**, cùng 3638 passed. Kết luận: nhiễu teardown không tất định (bộ test chạy
thứ tự ngẫu nhiên), không phải regression tái hiện được. Ghi lại để nếu tần suất tăng thì có mốc.

## 6. Verify

`ci-local.ps1 -Full` ×2: **3638 passed, 4 skipped** cả hai lần. Đã grep log thật tìm
`FAILED|ERROR|Traceback|ResourceWarning`.
