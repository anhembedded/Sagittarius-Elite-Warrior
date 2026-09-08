# EPIC-023B — Biểu đồ Vốn (equity) realtime trên Dev Board

- **Trạng thái:** ✅ **Đã xong (2026-09-08)** — xem §5 "Kết quả xây dựng".
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

---

## 5. Kết quả xây dựng (2026-09-08)

Đúng thiết kế §2/§3, cộng 1 bước dọn dẹp phát sinh khi build (§5.1 — cùng lý do `EPIC-023A` đã dời
`PositionsPanel`/`OpenOrdersPanel`).

| File | Việc |
| :--- | :--- |
| `src/presentation/ui/common/equity_chart_adapter.py` | **Dời** từ `screens/trading/` — xem §5.1 |
| `src/presentation/ui/screens/dashboard/dashboard_view.py` | `self.equity_chart` (đúng cách dựng `TradingView._build_equity_chart`), thêm vào `_workspace` dưới cụm chart card, **có stretch factor** ngay từ đầu (bài học `EPIC-023A` §5.3 — không lặp lại bug tương tự) |
| `src/presentation/ui/screens/dashboard/dashboard_presenter.py` | `self._equity_recorder = container.resolve(EquityCurveRecorder)`; seed `view.equity_chart` từ `.samples` **sau** `_connect_engine_events()` (đúng thứ tự chống miss sample `BUG-100` đã dạy); dựng `EquityFeed` riêng, nối `equitySampled` → `_on_equity_sampled` |

### 5.1 Phát sinh khi build: dời `equity_chart_adapter.py` ra `common/`

Y hệt lý do `EPIC-023A` đã dời `PositionsPanel`/`OpenOrdersPanel`: `equity_chart_adapter.py` là 2
hàm thuần (`EquitySample -> OhlcCandle`), không phụ thuộc `TradingViewModel`/`TradingPresenter`,
nhưng vật lý nằm trong `screens/trading/`. Dev Board cần đúng 2 hàm đó — dời sang `common/` (cùng
thư mục `order_fill_marker.py` đã ở sẵn, đúng tiền lệ có thật), sửa 3 import site
(`trading_presenter.py`, 2 file test).

### 5.2 Kiểm thử

- **Unit (Dev Board presenter):** 3 test mới trong `test_dashboard_presenter.py` — mirror
  `test_trading_presenter_equity.py`'s 3 test tương ứng (seed rỗng, seed backlog,
  `EquitySampledEvent` nối 1 điểm), dùng `monkeypatch` spy lên `view.equity_chart` (view thật).
  Thêm fixture `equity_recorder` (real `EquityCurveRecorder()`, không phải Mock — `.samples` phải
  là iterable thật) + nối vào `mock_container`'s `resolve_side_effect`; sửa luôn 1 test cũ
  (`test_boot_wires_the_container_registered_store_into_the_view`) tự dựng container riêng, cũng
  cần `EquityCurveRecorder` trong `resolve_side_effect` của nó.
- **Xác minh bằng mắt:** chụp lại `SEW_CAPTURE_SCREENSHOTS=...
  test_capture_screenshots.py::test_capture[dashboard]` — "Live Chart: Vốn" hiện đúng, có tiêu đề,
  không lặp lại lỗi squeeze `EPIC-023A` §5.3 đã tìm ra (đã cấp stretch factor ngay từ đầu).
- Toàn bộ cổng: `ruff check`/`ruff format --check` sạch, `mypy` — `Success: no issues found in 257
  source files`, `pytest tests/unit/presentation/ui/screens/test_dashboard_presenter.py
  tests/unit/presentation/ui/common/ tests/unit/presentation/ui/screens/trading/
  tests/unit/presentation/ui/screens/test_dashboard_view.py` — 257 passed.
