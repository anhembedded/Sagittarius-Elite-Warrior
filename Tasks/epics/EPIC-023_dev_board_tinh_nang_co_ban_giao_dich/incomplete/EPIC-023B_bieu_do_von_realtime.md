# EPIC-023B — Biểu đồ Vốn (equity) realtime trên Dev Board

- **Trạng thái:** 🔴 Backlog
- **Repo:** Elite
- **Chặn bởi:** — · **Chặn:** —

## 1. Việc cần làm

Thêm một `ChartCard` thứ hai (dạng line, không nến/volume — API đã có, xem
`trading_view.py::_build_equity_chart`) vào workspace Dev Board, seed từ
`EquityCurveRecorder.samples` lúc dựng Presenter, cập nhật sống qua `EquityFeed`
(`EquitySampledEvent`) — dựng instance `EquityFeed` riêng của `DashboardPresenter`, đúng khuôn
`OrderFeed` đã tự dựng từ `EPIC-021K`.

## 2. Thay đổi theo file

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/screens/dashboard/dashboard_view.py` | Thêm `self.equity_chart` (đúng cách dựng như `TradingView._build_equity_chart`), đặt trong workspace dưới bảng Vị thế/Lệnh chờ (`EPIC-023A`). |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | `self._equity_recorder = container.resolve(EquityCurveRecorder)`; seed chart từ `.samples` sau `_connect_engine_events()`; dựng `EquityFeed`, nối `equitySampled` → append. |

## 3. Quyết định thiết kế

- Dùng lại `equity_chart_adapter.py` (`EPIC-021M` §2.4 phương án 2) nguyên vẹn — hàm thuần
  `EquitySample -> OhlcCandle`, không phụ thuộc `TradingViewModel`/`TradingPresenter`. **Không**
  viết bản thứ hai.
- Không cần widget mới: `ChartCard` đã đủ API (`set_chart_type("line")`, `set_volume_visible(False)`,
  `toolbar.setVisible(False)`).

## 4. Kiểm thử

Cùng khuôn `test_trading_presenter_equity.py` — bản Dev Board: seed rỗng, seed có backlog,
`EquitySampledEvent` nối thêm đúng 1 điểm. Không sanity mới.
