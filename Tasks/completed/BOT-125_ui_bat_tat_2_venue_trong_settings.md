# BOT-125 — 2 control bật/tắt môi trường sàn trong Settings

- **Trạng thái:** ✅ Hoàn thành (2026-09-07)
- **Ngày lập:** 2026-09-07
- **Liên quan:** [`EPIC-021`](../epics/EPIC-021_ket_noi_binance_futures_testnet/README.md) (ADR §2, §3),
  [`EPIC-022`](../epics/EPIC-022_chien_luoc_song_tren_man_giao_dich/README.md)

---

## 1. Vấn đề thật

User vừa hoàn thành `EPIC-022` (chọn + nạp chiến lược trên màn Giao dịch), nạp chiến lược xong
vẫn **không bật được giao dịch**, vì `exchange.trading_venue` trong `app_config.json` đang là
`"disabled"` — và **không có chỗ nào trong app sửa được nó**.

Đây không phải suy đoán, `environment_banner_content.py` đã ghi thẳng trong docstring của chính
nó từ `EPIC-021K`:

> *"`EXCHANGE_MARKET_DATA_VENUE`/`EXCHANGE_TRADING_VENUE` are read only at boot
> (`resolve_market_data_venue`/`resolve_trading_venue`), Settings has no UI control for either
> (**grep confirms**), so both are file-edit-and-restart config."*

Nghĩa là để bật giao dịch, user phải: thoát app → mở `src/config/app_config.json` bằng editor →
sửa tay một chuỗi → khởi động lại. Với một tính năng mà cả `EPIC-021` lẫn `EPIC-022` được lập ra
để phục vụ, đó là cái cổng vào bị khoá bằng file JSON.

## 2. Hai giá trị này khác nhau, và đó là chủ ý (ADR §2)

| Key | Chọn được gì | Ý nghĩa |
| :--- | :--- | :--- |
| `exchange.market_data_venue` | `mainnet_public` / `futures_testnet` | Giá trên chart lấy từ đâu |
| `exchange.trading_venue` | `disabled` / `futures_testnet` | Lệnh đi đâu (hoặc **không đi đâu cả**) |

Tách **cố ý** (ADR §2): xem giá thật của mainnet trong khi lệnh chạy trên testnet là tổ hợp hợp
lệ và hữu ích — nhưng là tổ hợp **nguy hiểm**, nên `VenueAlignment` sinh ra banner đỏ cảnh báo
"giá thấy ≠ giá khớp". Gộp 2 cái thành 1 công tắc sẽ xoá mất khả năng đó, và xoá luôn lý do tồn
tại của banner.

`TradingVenue` **không có** member `MAINNET`, cũng cố ý (ADR §3): giao dịch tiền thật phải là một
epic có review, không phải một dòng config ai cũng sửa được. Nên control thứ 2 thực chất đúng là
một công tắc **bật/tắt**, đúng như user mô tả.

## 3. Thiết kế

### 3.1 Đặt ở Settings, không phải màn Giao dịch

Màn Giao dịch đã có công tắc "Bật giao dịch" — đó là công tắc **phiên** (`TradingSessionState`,
cố ý không nhớ giữa các phiên, `EPIC-021G` §2.3). Hai giá trị này là **cấu hình môi trường**, đọc
lúc boot, ảnh hưởng cả app (banner ở cả 5 màn, `ExchangeSessionFactory`, đăng ký DI của
`ITradingClient`). Hai tầng khác nhau: đặt cạnh nhau sẽ khiến user tin rằng chúng cùng loại.

### 3.2 Nói thật về việc cần khởi động lại

Đổi 2 giá trị này **không thể** có hiệu lực ngay, và lý do rất cụ thể:
`binance_bot_module.py:432` chỉ đăng ký `ITradingClient` vào DI container **khi**
`trading_venue is not DISABLED`, và container đã dựng xong từ lúc boot. `ExchangeSessionFactory`
cũng nhận `market_data_venue` lúc dựng.

Nên UI **phải nói ra**, không được để user tưởng đã đổi xong (`domain-truth-rule.md` — "Truthful
Trading UI"). Nhãn cảnh báo sẵn có ở đầu màn Settings đang chỉ nói về API Key/Secret; mở rộng cho
đúng 2 field mới này.

**Không chọn hướng "áp dụng nóng"**: phải dựng lại `ExchangeSessionFactory`, đăng ký lại
`ITradingClient`, tính lại `VenueAlignment` cho banner ở 5 màn, và xử lý trường hợp đang có vị
thế mở lúc đổi. Đó là một epic riêng, không phải phần phụ của 2 combobox.

### 3.3 Rào an toàn

Không cho đổi khi **giao dịch đang bật** — cùng lý do `EPIC-022` §4.1 cấm đổi chiến lược giữa
chừng. Đổi nơi đặt lệnh trong khi một phiên giao dịch đang chạy là thay đổi ý nghĩa của mọi thứ
đang diễn ra.

## 4. Đổi theo file

- `settings_view_model.py` — 2 property + options, vào chung `load_fields()`.
- `settings_view.py` — 2 `QComboBox`, nhãn tiếng Việt, mở rộng nhãn cảnh báo khởi động lại.
- `settings_presenter.py` — đọc lúc `_load_from_config()`, ghi trong `_on_save()`.
- `venue_labels.py` (mới) — nhãn tiếng Việt cho từng member enum, một nguồn duy nhất.

## 5. Test

- Load: config có sẵn ⇒ combo đúng giá trị; giá trị lạ trong config ⇒ rơi về mặc định an toàn
  (`disabled`), không crash.
- Save: ghi đúng 2 key + `save()`; **không** đổi được khi `TradingSessionState.enabled`.
- Nhãn: mỗi member của cả 2 enum đều có nhãn (guard chống thêm member mà quên nhãn).

---

## 6. Implementation Notes (2026-09-07)

**Lỗi thật gặp khi làm, không phải giả định.** 7 test Settings sẵn có đổ đỏ ngay sau khi
Presenter đọc thêm `TradingSessionState`: container giả trong test trả `Mock()` cho mọi interface
lạ, nên `session_state.enabled` là một `Mock` — truthy — và `setVisible(Mock)` ném `TypeError`.
Sửa bằng cách cho 5 container ad-hoc trong 2 file test trả `TradingSessionState()` thật. Đây đúng
là bẫy `ONBOARDING.md` §4 mô tả: một `Mock` không chạy thân hàm thật, và ở đây nó còn khiến
nhánh "đang giao dịch" luôn được chọn — test sẽ xanh cho một hành vi sai.

**Một assertion của chính tôi sai và bị test bắt.** Test đầu tiên assert `save_count == 1`, nhưng
`SettingsPresenter._on_save()` chỉ gọi `save()` khi `isinstance(self.config, ConfigManager)` —
docstring của chính nó nói rõ một `IConfig` thay thế "simply won't persist, which is the correct
behaviour for those". Assertion đó đang kiểm tra fake chứ không kiểm tra app; đã bỏ và ghi lý do
ngay tại chỗ.

**Bỏ một assertion vô nghĩa.** `view._venue_lock_label.isVisible()` luôn `False` khi cửa sổ chưa
từng được show, nên `assert ... is False or True` là tautology. Thay bằng assert nội dung nhãn
thật sự được đặt.

**Kết quả:** 7 test mới, CI đầy đủ xanh (3615 passed, 4 skipped), đã grep log thật tìm
`FAILED|ERROR|Traceback|ResourceWarning`.
