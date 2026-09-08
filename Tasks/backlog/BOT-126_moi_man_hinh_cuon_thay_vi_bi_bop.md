# BOT-126 — Mọi màn hình phải cuộn khi tràn, thay vì bị bóp dẹp

**Trạng thái:** 🟡 Đang làm (2026-09-08)
**Nguồn:** user báo *"màn Giao dịch UI xấu, mọi thứ quá chen chúc"* kèm ảnh chụp app thật, và yêu cầu *"mọi vùng phải cuộn được, hiện chỉ Backtest có"*.
**Rủi ro:** 🟠 — đụng `PageShell`, tức cả 5 màn hình.

---

## 1. Tiền đề ban đầu sai, nhưng triệu chứng là thật

User nói *"chỉ Backtest có cơ chế cuộn"*. **Không đúng:** cả 5 màn đều đã được bọc
`QScrollArea` — `PageShell.set_workspace()` tự bọc `main`/`rail`, và Backtest/Dashboard/Settings
còn tự dựng một cái của riêng mình.

Vấn đề nằm ở chỗ khác, và nó giải thích đúng vì sao **trông như** chỉ Backtest cuộn được:

> `QScrollArea.setWidgetResizable(True)` co nội dung cho vừa viewport, và **chỉ** cuộn khi
> **kích thước tối thiểu** của nội dung không còn vừa. Một cột card mà mỗi card đều co được có
> minimum thấp hơn hẳn chiều cao nó muốn → Qt bóp dẹp nó và **thanh cuộn không bao giờ xuất hiện**.

Backtest cuộn được **không phải vì nó có cơ chế riêng**, mà vì nội dung của nó tình cờ có minimum
1256px — đủ lớn để Qt không còn chỗ mà bóp.

## 2. Đo thật trên app thật (không suy đoán)

Boot app thật bằng `app_bootstrapper.build()` ở `QT_QPA_PLATFORM=offscreen`, đi qua từng route,
đọc `sizeHint` / `minimumSizeHint` của nội dung và range của thanh cuộn dọc.

**Cửa sổ 1920×1080, trước khi sửa:**

| Màn (vùng) | Muốn cao | Tối thiểu | Viewport | Kết quả |
| :--- | ---: | ---: | ---: | :--- |
| backtest (chính) | 1265 | 1256 | 947 | ✅ cuộn — minimum quá lớn để bóp |
| **trading (rail 3 card)** | **1178** | **302** | 647 | ❌ **bị bóp mất 531px, không có thanh cuộn** |
| dashboard (giữa) | 802 | 798 | 659 | ✅ cuộn |
| data_management | 592 | 592 | 686 | vừa đủ |
| settings | 521 | 488 | 947 | vừa đủ |

Khớp chính xác với ảnh user gửi: rail màn Giao dịch bị cắt ngay sau nút "Nạp chiến lược" — 2 card
"TÍN HIỆU GẦN NHẤT" và "PHIÊN GIAO DỊCH" **không nhìn thấy được bằng bất kỳ cách nào**, vì không có
thanh cuộn để kéo tới.

## 3. Sửa: một cơ chế ở `kit/`, không phải 5 bản sao ở 5 màn

`kit/preferred_height_scroll_area.py` — `PreferredHeightScrollArea(QScrollArea)`: giữ
`minimumHeight` của nội dung bằng đúng `sizeHint()` của nó, đồng bộ lại sau mỗi `LayoutRequest` /
`Resize` của chính nội dung (không phải của scroll area — chiều cao một cột card đổi khi **layout
của nó** chạy lại, không nhất thiết trùng lúc scroll area đổi kích thước).

Chống lặp vô hạn: chỉ ghi khi giá trị thật sự đổi. `sizeHint()` đọc layout của nội dung và **không**
phụ thuộc `minimumHeight` của chính widget đó, nên một lần ghi là ổn định, không leo thang.

**Chart vẫn co giãn.** `setWidgetResizable(True)` vẫn kéo nội dung ra khi viewport cao hơn minimum,
và layout bên trong vẫn chia phần dư cho thứ nào co giãn được. Cái duy nhất chart mất đi là khả năng
bị nén xuống **dưới** chiều cao nó xin. Đây là điều user chốt khi được hỏi (2026-09-08): áp cho tất
cả, trừ chart.

Áp ở 4 chỗ, hết:

- `PageShell._scrollable()` — bọc tự động (Trading, Data Management);
- `dashboard_view.py`, `backtest_view.py`, `settings_view.py` — 3 màn tự dựng `QScrollArea`, đổi
  sang lớp mới để hành vi **giống hệt nhau ở mọi màn**, thay vì phụ thuộc nội dung màn nào tình cờ
  khó co hơn.

## 4. Kiểm chứng

**Đo lại sau khi sửa, cùng probe, cùng 1920×1080:** rail Giao dịch chuyển từ *bị bóp* sang **cuộn
được**. Bốn màn còn lại không đổi hành vi.

**Ảnh chụp app thật sau khi sửa:** rail hiện **đủ cả 3 card**; vùng chính có thanh cuộn và chart cao
hơn hẳn.

**Test** (`tests/unit/presentation/ui/kit/test_preferred_height_scroll_area.py`): 5 test, trong đó
có một **test baseline khoá chính cái defect** — `QScrollArea` trần với đúng nội dung đó **không**
cuộn. Test này bắt được một sai lầm thật khi viết: bản nháp đầu dùng `setFixedHeight()` cho từng
dòng, khiến minimum = preferred, nên nội dung cuộn được ngay cả với `QScrollArea` trần — tức test
sẽ xanh mà **không chứng minh gì cả**. Baseline đỏ đã lộ ra điều đó và nội dung test được viết lại
bằng `_CompressibleRow` (xin 40px, co được xuống 5px).

Cổng `ci-local.ps1 -Full` xanh, có grep `LOG_FILE`.

## 5. Hai thứ **không** nằm trong phạm vi task này (đã thấy trên ảnh, chưa sửa)

1. **Bảng bị cắt ngang.** Tiêu đề cột hiện ra "KHỐI LU", "CHI", "KIỂU L" — cắt cụt giữa chữ. Do
   thanh cuộn ngang bị tắt cứng (`ScrollBarAlwaysOff`) trong khi cột không tự co. Đây là lỗi
   **chiều ngang**, cơ chế khác hẳn, và `ui-presentation-rule.md` đã có luật riêng về độ rộng cột
   (Single Source of Truth, bind cho cả header lẫn row). Cần task riêng.
2. **Băng console chiếm chỗ cố định.** Trong ảnh, "NHẬT KÝ GIAO DỊCH" chiếm ~350px và gần như trống,
   trong khi vùng làm việc phía trên bị dồn. Đây là câu hỏi **phân bổ không gian giữa các băng của
   `PageShell`**, không phải chuyện cuộn.
