# EPIC-022C — Thăng cấp form thông số + tính toán overlay ra khỏi `screens/backtest/`

**Status:** ✅ Hoàn thành (2026-09-07) · **Chặn bởi:** — (song song được) · **Repo:** Elite

---

## 1. Vấn đề

4 module dưới đây **không phụ thuộc gì vào màn Backtest** (đọc `strategy_cls`/`klines`, trả về dữ
liệu thuần) nhưng lại nằm trong `screens/backtest/`. Màn Giao dịch cần đúng 4 thứ này, mà import
chéo `screens/trading/ → screens/backtest/` là thứ [`EPIC-021L`](../../EPIC-021_ket_noi_binance_futures_testnet/completed/EPIC-021L_dao_chieu_phu_thuoc_qml_screens.md)
vừa dọn xong (`BUG-082`) — tái phạm là đi lùi.

`architecture-rule.md` §5: *"một thư mục là một tầng, không phải cái sọt"*. `screens/backtest/`
đang là cái sọt cho 4 món dùng chung.

## 2. Thiết kế — chỉ đổi chỗ, không đổi hành vi

| Từ | Sang | Vì sao chỗ mới đúng |
| :--- | :--- | :--- |
| `screens/backtest/logic/bot_params_form.py` | `components/strategy_params/bot_params_form.py` | Sinh schema/rows/parse từ `BaseStrategy.inputs` — thuần metadata, không biết màn nào |
| `screens/backtest/backtest_modals/_bot_param_field.py` | `components/strategy_params/param_field.py` | 1 widget 1 ô nhập; bỏ tiền tố `_` vì nay là API công khai của component |
| `screens/backtest/logic/strategy_indicator_lines.py` | `components/strategy_overlay/strategy_indicator_lines.py` | Replay chiến lược ra (x, y) để vẽ — dùng chung 2 màn |
| `screens/backtest/logic/strategy_trend_zones.py` | `components/strategy_overlay/strategy_trend_zones.py` | Như trên, cho vùng tô nền |

2 thư mục riêng chứ không gộp 1: form thông số (nhập liệu) và overlay chart (hiển thị) là **2
tầng trừu tượng khác nhau**, §5 cấm ở chung `dir`.

**Không để lại module shim re-export.** Shim là bản sao thứ 2 của đường dẫn, đúng loại "drifted
copy" mà `CLAUDE.md` mở đầu bằng việc cảnh báo. Sửa thẳng import ở mọi call site (`grep` ra hết,
`mypy` bắt phần sót).

## 3. Đổi theo file

- 4 `git mv` + sửa `import` trong: `backtest_presenter.py`, `coordinators/strategy_config_coordinator.py`,
  `coordinators/indicator_coordinator.py`, `coordinators/chart_feed_coordinator.py`,
  `backtest_modals/strategy_properties_dialog.py`, `backtest_modals/__init__.py`, và các file test
  tương ứng trong `tests/unit/presentation/ui/screens/`.
- 2 `__init__.py` mới cho 2 component package.

## 4. Test

Không viết assert mới cho hành vi (không có hành vi nào đổi). Bằng chứng đúng ở đây là
**bộ test cũ xanh nguyên trạng, 0 assert bị sửa** — cùng kiểu bằng chứng `BOT-124` đã dùng khi
trích `DataTable` dùng chung. Chỉ sửa dòng `import` trong test.
