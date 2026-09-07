# EPIC-003G2 — `DashboardPresenter` → `logic/chart_zoom_limits.py`

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Nối tiếp:** [`EPIC-003G`](EPIC-003G_dashboard_presenter_coordinator.md)
**Trạng thái:** ✅ Xong 2026-09-07 · **Rủi ro:** 🟢

---

## 1. Đối tượng: hai bản sao của một phép tính

`_ensure_chart_cards()` và `_on_timeframe_changed()` cùng viết:

```python
from ...config_keys import ConfigKeys          # import trong thân hàm
from ...timeframe import TimeFrame             # import trong thân hàm
bar_seconds = TimeFrame(<interval>).to_seconds()
max_candles = self.config.get(ConfigKeys.CHART_CARD_MAX_ZOOM_OUT_CANDLES.value, 2000, cast=int)
card.set_max_visible_x_range(max_candles * bar_seconds)
```

Ba vấn đề trong 5 dòng, nhân đôi:

1. **Import trong thân hàm** — `code-quality-rule.md` cấm thẳng ("no function-local imports"). Đây
   là **2 trong 2** chỗ duy nhất còn vi phạm trong file này.
2. **Số ma thuật `2000`** viết tay hai lần.
3. **Hai chủ sở hữu cho một quy tắc.** Card dựng lúc khởi động và card đổi tầm sau khi bấm timeframe
   sẽ bất đồng về mức zoom-out tối đa nếu chỉ một bản được sửa — cùng một màn hình, không gì phát
   hiện ra.

## 2. Kết quả

| File | Việc |
| :--- | :--- |
| `.../dashboard/logic/chart_zoom_limits.py` | **Mới** — `max_visible_x_range(config, interval)` + `DEFAULT_MAX_ZOOM_OUT_CANDLES` |
| `.../dashboard/dashboard_presenter.py` | 1.222 → **1.207 dòng**; 2 khối 5 dòng còn 2 dòng; hết import trong thân hàm |
| `tests/.../dashboard/logic/test_chart_zoom_limits.py` | **Mới** — 3 test, gồm bất biến "cap tính bằng **nến**, không phải bằng giây" (1h phải rộng gấp 60 lần 1m) |

**`tests/` diff rỗng tuyệt đối.** Test hiện có
`test_config_max_zoom_out_candles_applied_to_chart_cards` vẫn xanh không sửa dòng nào.
