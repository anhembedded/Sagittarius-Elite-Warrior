# EPIC-003E2 — `BackTestPresenter` → `logic/run_config_builder.py`

**Thuộc Epic:** [`EPIC-003`](../README.md) · **Nối tiếp:** [`EPIC-003E`](EPIC-003E_backtest_presenter_coordinator.md)
**Trạng thái:** ✅ Xong 2026-09-07 · **Rủi ro:** 🟡

---

## 1. Vì sao vẫn còn việc sau `003E`

`003E` đã tách 6 Coordinator và đưa file từ 2.803 → 2.135 dòng. Nhưng nó tách theo **luồng việc**
(chạy, đồng bộ, vẽ chart, trade log…), nên phần **đọc và kiểm tra form** ở lại nguyên: đo lại
2026-09-07, `_build_run_config` **107 dòng** và `_get_current_config` **36 dòng** — ~7% của một file
1.966 dòng, và không hàm nào chạm state của Presenter ngoài 3 giá trị.

`code-rule.md` §3 nói rõ `logic/` là chỗ cho **biến đổi thuần**. Đây đúng là biến đổi thuần bị kẹt
trong Presenter.

## 2. Điều làm nó không test được, và cách bỏ

Bản cũ **ghi thẳng** lỗi ra ngoài giữa lúc parse:

```python
self._log_dev_trace("run_config_invalid", reason=..., capital=...)
view_model.set_result(issue.message, is_error=True)
return None
```

Nên muốn assert "capital rỗng thì bị từ chối" phải dựng cả một Presenter (thread manager,
dispatcher, FSM, view). Bản mới **trả về** chuyện đã xảy ra — `RunConfigOutcome(config,
error_message, traces)` — còn Presenter thực hiện đúng 2 side effect đó, **đúng thứ tự cũ**:

```python
outcome = build_run_config(self._view_model, symbol=..., strategy_params=..., execution_mode=...)
for trace in outcome.traces:
    self._log_dev_trace(trace.event, **trace.fields)
if outcome.config is None:
    self._view_model.set_result(outcome.error_message, is_error=True)
    return None
return outcome.config
```

## 3. Hai hàm, không gộp làm một

| Hàm | Tính chất | Dùng cho |
| :--- | :--- | :--- |
| `build_run_config()` | **Nghiêm** — chạy `PreBacktestAssertionPipeline`, từ chối chứ không đoán | Thật sự bắt đầu một lần chạy |
| `snapshot_current_config()` | **Dễ dãi** — không bao giờ lỗi, có fallback (`10000.0`, `Currency.USD`, `timeframe_or_fallback`) | Chỉ để dựng nhãn dirty-tracking |

Gộp lại thì hoặc một lần chạy bắt đầu trên giá trị đoán, hoặc cái nhãn không vẽ được khi form đang
điền dở. `broker_config` của bản snapshot **cố ý** là `BrokerSimulationConfig()` mặc định — đó chính
là lý do `_fee_rate_percent_for_last_run` tồn tại, và giờ có test ghim điều đó lại.

## 4. Hợp đồng tường minh thay vì duck-typing

`RunConfigInputs` là một `Protocol` liệt kê **đúng 18 thuộc tính** hai hàm này đọc — không nhận
`BackTestViewModel` (`architecture-rule.md`: hợp đồng tường minh, không duck-typing ngầm). Nhờ vậy
test đưa vào một `dataclass` trần, và danh sách đó cũng chính là những gì một lần tách ViewModel
sau này phải giữ nguyên đường đọc.

## 5. Kết quả

| File | Việc |
| :--- | :--- |
| `.../logic/run_config_builder.py` | **Mới** — 2 hàm public + `RunConfigInputs`/`RunConfigOutcome`/`DevTrace`, `published_candle_cutoff()` |
| `.../backtest_presenter.py` | 1.966 → **1.828 dòng**; 2 hàm còn lại là delegate; xoá `_parse_custom_datetime`, `_published_candle_cutoff`, `_NO_STRATEGY_MESSAGE`, `_LIVE_BACKTEST_END_DELAY_INTERVALS` |
| `tests/.../backtest/logic/test_run_config_builder.py` | **Mới** — 15 test, kể cả `now` bơm vào để assert được mốc nến đã publish thay vì đua với đồng hồ thật |

**`tests/` diff rỗng tuyệt đối** — không sửa dòng test nào có sẵn.

### 5.1 Một test của chính tôi sai trước, code đúng

`test_a_custom_range_uses_the_typed_boundaries_verbatim` viết `"2026-01-01 00:00:00"`; định dạng
thật là `%Y-%m-%d %H:%M` (không có giây). Test đỏ, đọc `DATETIME_FORMAT` rồi sửa test — không nới
parser cho khớp test.
