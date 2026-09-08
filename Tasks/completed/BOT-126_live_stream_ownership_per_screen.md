# BOT-126: `ILiveStreamService` — sở hữu stream theo từng màn, không còn "ai gọi sau cùng thắng"

**Trạng thái:** ✅ Hoàn thành (2026-09-08)

## 1. Bối cảnh & vấn đề thật

`EPIC-021I` §6.4 đã ghi nhận (không sửa, ngoài phạm vi epic đó): `ILiveStreamService`
(`start_stream(symbols, interval)`/`stop_stream()`) là **một** stream toàn tiến trình, không có
tham số định danh người gọi. Dev Board và màn Giao dịch mở cùng lúc, mỗi bên đổi symbol/khung
thời gian độc lập, sẽ giành nhau cùng một luồng — màn nào gọi `StartLiveStreamCommand` sau cùng
quyết định symbol/khung nào chảy vào **cả hai** chart; `stop()` của một màn dừng luôn stream
chung, kể cả khi màn kia đang cần nó. `chart_coordinator.py` (Trading) tự ghi lại đúng ràng buộc
này trong docstring của chính nó khi build (`EPIC-021I`).

Yêu cầu thiết kế lại (từ user, việc này lớn hơn 1 bug fix vì đổi thẳng public contract
`ILiveStreamService`):

1. Hai màn có thể mỗi màn giữ 1 symbol live riêng, không giành tick của nhau.
2. Một màn đóng lại / tắt live của riêng nó không được dừng stream màn kia.
3. `StopLiveStreamCommand` (hiện "dừng hết, không tham số") phải đổi sang scope theo màn.

**Chốt sở hữu:** `ILiveStreamService` khai trong `src/application/ports/` (layer Application của
app này) — **không** phải type của `Sagittarius_Engine`. `BinanceWebsocketService` (implementer)
cũng ở `src/infrastructure/`. Toàn bộ thay đổi nằm gọn trong repo `Sagittarius_Elite_Warrior`,
không đụng Engine.

### 1.1. Lỗ hổng đồng dạng phát hiện thêm khi rà — bắt buộc sửa cùng lượt

`DashboardPresenter._handle_market_tick`/`TradingPresenter._handle_market_tick` lọc tick **chỉ
theo `symbol`**, không theo `interval` — y hệt root cause `BUG-085` (đã vá cho
`MarketTickEventHandler` ở tầng chiến lược, **chưa** vá ở 2 Presenter UI này). Vô hại từ trước
tới giờ vì chỉ có 1 stream toàn tiến trình nên không bao giờ có 2 interval cùng symbol chạy song
song. Thiết kế multiplex+refcount bên dưới làm khả năng đó **trở thành hiện thực lần đầu tiên**
(vd Dev Board mở `BTCUSDT@1m`, Trading mở `BTCUSDT@5m`) — nên đây là phần bắt buộc của scope
(`ONBOARDING.md` §12.5 điểm 1: "Fix the mechanism" — cùng lỗi xuất hiện ở ≥2 nơi), không phải dọn
dẹp thêm.

## 2. Thiết kế

### 2.1. `ILiveStreamService` — đổi từ "1 stream" sang "tập (symbol, interval) đếm tham chiếu theo owner"

Binance's socket manager vốn đã hỗ trợ 1 kết nối multiplex mang nhiều `symbol@kline_interval`
cùng lúc (`BinanceWebsocketService._create_socket` đã dùng `multiplex_socket` khi ≥2 stream) —
tận dụng đúng khả năng đó thay vì mở nhiều kết nối song song.

```python
class ILiveStreamService(ABC):
    def subscribe(self, owner: str, symbols: list[str], interval: TimeFrame) -> bool: ...
    def release_owner(self, owner: str) -> bool: ...
    def stop_all(self) -> bool: ...
```

- `subscribe(owner, symbols, interval)`: **thay thế** toàn bộ tập đăng ký cũ của đúng `owner` này
  bằng tập mới — gọi lại không cần `release_owner` trước (Dev Board/Trading vẫn tự nhiên gọi
  "stop rồi start" khi đổi khung/symbol như hiện tại, nhưng giờ **không bắt buộc** nữa vì
  `subscribe` tự thay thế).
- `release_owner(owner)`: rút đúng phần đăng ký của `owner`, không đụng owner khác. Trả `False`
  nếu owner đó vốn không có gì đang chạy (giữ nguyên ngữ nghĩa DEBUG-vs-nothing-to-do hiện có của
  `stop_stream()`).
- `stop_all()`: dọn sạch không quan tâm owner — dùng đúng 1 chỗ, `LiveStreamEngineAdapter.stop()`
  (Engine shutdown, lúc đó không owner nào còn quan trọng nữa).

Bên trong `BinanceWebsocketService`: `_subscriptions: dict[tuple[str, str], set[str]]` (key =
`(symbol, interval.value)`, value = tập owner đang cần cặp đó) + `threading.Lock` (tiền lệ
`InFlightSyncGuard`, `BOT-121` — registry dùng chung giữa nhiều thread gọi `dispatcher.dispatch`
từ các `IThreadManager.submit` khác nhau). Mỗi lần `subscribe`/`release_owner` mutate registry,
tính lại **tập khoá đang cần chạy**; nếu khác tập đang chạy thật (`self._active_keys`) thì huỷ
task cũ (nếu có) và spawn task mới với `streams` tổng hợp từ tập mới — giữ nguyên cơ chế
cancel-token + `ITaskManager.spawn` hiện có, chỉ đổi **cái gì kích hoạt** việc restart (tập khoá
thay đổi, không phải "ai gọi sau cùng"). Nếu tập không đổi (vd owner thứ 2 xin đúng cặp
`(symbol, interval)` owner thứ nhất đã có) → không restart, không mất tick.

`_run_stream`/`_create_socket` đổi từ `(symbols: list[str], interval: TimeFrame)` sang
`keys: list[tuple[str, str]]` (mỗi phần tử tự mang interval riêng của nó) — vẫn dùng
`kline_socket` khi đúng 1 khoá, `multiplex_socket` khi ≥2, không đổi logic reconnect.

**Đánh đổi được chấp nhận, không phải bug:** khi tập khoá đang chạy đổi (1 owner thêm/bớt), task
multiplex bị huỷ và spawn lại — **mọi** owner khác đang share kết nối đó mất tick trong khoảnh
khắc reconnect (thường < 1s, cùng độ trễ reconnect đã có sẵn khi mất mạng). Không làm mất đăng ký
của owner khác (owner đó vẫn có trong tập mới, tick tiếp tục chảy sau khi task mới lên), chỉ là
gián đoạn ngắn — đúng yêu cầu #2 ("không dừng stream màn kia"), không đúng nghĩa "0 gián đoạn
tuyệt đối". Ghi lại theo `architecture-rule.md` §7 (giá đã biết phải trả) bằng 1 test khoá hành vi
này, không chỉ 1 dòng comment.

### 2.2. `StartLiveStreamCommand`/`StopLiveStreamCommand` — thêm/đổi tham số `owner`

- `StartLiveStreamCommand(owner: str, symbols: list[str], interval: TimeFrame)` — `owner` bắt
  buộc, validate non-empty giống `symbols`.
- `StopLiveStreamCommand(owner: str)` — bỏ hẳn dạng "không tham số", scope theo màn đúng yêu cầu
  #3. Handler gọi `stream_service.release_owner(request.owner)`.
- Mỗi call site tự đặt `owner` cố định của chính nó (hằng số module, không phải UUID — mỗi loại
  màn chỉ có đúng 1 instance sống cùng lúc trong app này):
  - `chart_coordinator.py` (Trading): `"trading"`.
  - `stream_lifecycle_controller.py` (Dev Board): `"dashboard"` (khớp `StateScope(key="dashboard")`
    đã dùng ở `dashboard_presenter.py`).
  - `stream_cli_handler.py`/`stream_cmd.py` (CLI, tiến trình riêng, không chạy chung với UI):
    `"cli"`.

### 2.3. Vá lỗ hổng lọc-theo-interval ở 2 Presenter (đồng dạng `BUG-085`)

`DashboardPresenter._handle_market_tick`/`TradingPresenter._handle_market_tick`: thêm
`md.interval != self._active_interval → return`, đặt cạnh bộ lọc `symbol` đã có — đúng vị trí
`BUG-085` đã vá cho `MarketTickEventHandler`.

### 2.4. Hệ quả tự nhiên, không cần code thêm

`ChartCoordinator.stop()`/`StreamLifecycleController._on_stop_stream()` gọi
`StopLiveStreamCommand(owner=...)` giờ **luôn an toàn** — không còn khả năng dừng nhầm stream màn
khác. `_restart_chart()` (Trading)/`_on_timeframe_changed()` (Dev Board) tiếp tục stop-rồi-start
như cũ, không cần sửa gì thêm — chính là lý do "the guard is a workaround, not a fix" trong yêu
cầu ban đầu: sửa đúng cơ chế thì workaround (nếu có) hết cần thiết.

## 3. Ngoài phạm vi

- Không thêm cơ chế subscribe/unsubscribe không-reconnect ở tầng giao thức Binance (gửi frame
  `SUBSCRIBE`/`UNSUBSCRIBE` trên kết nối combined-stream đang mở) — `python-binance`'s
  `BinanceSocketManager` không lộ API đó tiện dụng; giữ cơ chế restart-task hiện có, chỉ đổi điều
  kiện kích hoạt. Ghi lại ở §2.1 làm điểm mở rộng sau nếu gián đoạn reconnect thành vấn đề thật.
- Không đổi `IHostedService`/`ITaskManager` (Engine) — vẫn 1 task nền cho kết nối đang hoạt động,
  chỉ đổi nội dung `streams` nó mang.
- Không thêm state persistence (nhớ owner/symbol giữa các phiên) — ngoài phạm vi việc này.
- Không đổi hành vi "Trading screen không tự dừng stream khi navigate away" (giữ nguyên UX hiện
  tại, chỉ sửa lại docstring giải thích lý do cho đúng thiết kế mới).

## 4. Kiểm thử

- `BinanceWebsocketService`: viết lại `test_binance_websocket_service.py` theo API mới —
  2 owner cùng xin `(BTCUSDT, 1m)` → chỉ 1 lần spawn; owner A rút, owner B còn → **không** restart
  task cho tới khi B cũng rút hoặc đổi; owner A đổi symbol trong khi owner B không đổi → B vẫn có
  trong tập mới sau restart; `stop_all()` dọn sạch bất kể owner.
- `StartLiveStreamCommandHandler`/`StopLiveStreamCommandHandler`: cập nhật theo `owner`, mock
  `ILiveStreamService.subscribe`/`release_owner` được gọi đúng tham số.
- `DashboardPresenter`/`TradingPresenter`: 1 test mỗi màn — tick cùng symbol khác interval bị
  chặn (mirror đúng kỹ thuật test `BUG-085` đã dùng cho `MarketTickEventHandler`).
- `tests/integration/test_app_integration.py`: cập nhật `owner="test"` cho cả 2 command.
- Gate đầy đủ: `ruff check`/`ruff format --check` các file đổi, `mypy` (`src` + `scripts` cùng
  lệnh), rồi `pytest` các thư mục liên quan.

## 5. Ghi chú Triển khai — 2026-09-08

Thiết kế đã trình bày và **được user duyệt** trước khi code (§0 — thay đổi public contract, theo
`ONBOARDING.md` §7/§12.5.3). Triển khai đúng theo §2, không lệch.

### 5.1. File đổi

- `src/application/ports/i_live_stream_service.py`: thay `start_stream`/`stop_stream` bằng
  `subscribe`/`release_owner`/`stop_all` như §2.1.
- `src/infrastructure/binance/binance_websocket_service.py`: viết lại theo registry
  `dict[(symbol, interval), set[owner]]` + `threading.Lock` + `_apply_active_set_locked()`
  (restart chỉ khi tập khoá đổi thật). `_run_stream`/`_create_socket` đổi từ
  `(symbols, interval)` sang `keys: list[tuple[str, str]]`.
- `src/infrastructure/engine_adapters/live_stream_adapter.py`: `stop_stream()` →
  `stop_all()` (Engine shutdown).
- `src/application/use_cases/stream/{start,stop}_live_stream/command.py`: thêm `owner: str`
  (validate non-empty); `StopLiveStreamCommand` bỏ hẳn dạng không tham số.
- `src/application/use_cases/stream/{start,stop}_live_stream/handler.py`: forward `owner` vào
  `subscribe`/`release_owner`.
- Call site tự đặt owner cố định: `chart_coordinator.py` → `"trading"`,
  `stream_lifecycle_controller.py` → `"dashboard"`, `stream_cli_handler.py`/`stream_cmd.py` →
  `"cli"`.
- `dashboard_presenter.py`/`trading_presenter.py::_handle_market_tick`: thêm bộ lọc
  `md.interval != self._active_interval → return` (đồng dạng `BUG-085`, §1.1/§2.3).
- `trading_presenter.py::shutdown()`: sửa lại docstring — không còn "dừng sẽ giết stream màn
  khác", giữ nguyên hành vi (không tự stop khi navigate away, khớp Dev Board).
- `Tasks/epics/.../completed/EPIC-021I_man_giao_dich_moi.md` §6.4: thêm dòng "Cập nhật" trỏ về
  task này — tránh để tài liệu đã đóng tiếp tục nói "chưa giải quyết" trong khi đã xong
  (`ONBOARDING.md` §12.2 — tránh bản ghi trạng thái trôi).

### 5.2. Test mới/sửa — 62 test

- `tests/unit/infrastructure/binance/test_binance_websocket_service.py`: viết lại theo API mới
  (9 test cho `subscribe`/`release_owner`/`stop_all`/`_create_socket`, giữ nguyên các test
  `_process_socket_message`/`_parse_kline`/reconnect cũ, chỉnh theo chữ ký `keys` mới) — 31 test,
  tất cả pass.
- `tests/unit/application/use_cases/stream/start_live_stream/test_command.py` (+1 test owner
  rỗng), `test_handler.py` (mới, 2 test forward đúng tham số).
- `tests/unit/application/use_cases/stream/stop_live_stream/` (thư mục test mới):
  `test_command.py` (4 test), `test_handler.py` (2 test).
- `tests/unit/presentation/ui/screens/trading/test_trading_presenter_chart_ticks.py` (mới, 3
  test khoá bộ lọc interval).
- `tests/unit/presentation/ui/screens/test_dashboard_presenter.py` (+2 test cùng mục đích, file
  Dashboard đã có sẵn fixture `presenter`).
- `tests/integration/test_app_integration.py`: cập nhật `owner="test"` cho cả 2 command.

**Một lỗi test tự bắt được khi chạy thật** (không phải bug ở code sản phẩm):
`test_stop_all_tears_down_regardless_of_owner` ban đầu viết 2 owner subscribe **2 khoá khác
nhau** rồi assert `handle.cancel.call_count == 1` — nhưng khoá đổi giữa 2 lần subscribe tự nó đã
kích hoạt 1 lần restart (1 lần cancel), cộng `stop_all()` là lần cancel thứ 2, trên cùng 1 mock
`handle` (do `task_manager.spawn.return_value` cố định) — asserted sai, không phải code sai. Sửa
test dùng chung 1 khoá cho cả 2 owner (không restart giữa chừng) để phép đo còn lại chỉ đúng
`stop_all()`'s riêng nó.

### 5.3. Xác minh — môi trường Linux thật, dựng từ đầu trong phiên này

Không có `.venv`/`Sagittarius_Engine` sẵn trong container — dựng theo đúng layout 2-repo lồng
nhau `ONBOARDING.md` §2/§9 mô tả: `python3.12 -m venv .venv` (Engine yêu cầu `>=3.12`, container
có sẵn), `pip install -r requirements.txt` (cả 2 repo), clone `anhembedded/Sagittarius_Engine`
(đọc, ẩn danh) và symlink `sagittarius_engine` package thẳng vào `/home/user/` (cùng cấp
`Sagittarius_Elite_Warrior/`) để `PYTHONPATH=.` từ `/home/user` khớp đúng lệnh mẫu ở §5 — **không**
`pip install -e` Engine: editable-install hiện đại dùng meta-path finder mà `mypy` không lần theo
được, khiến `py.typed` bị coi là "thiếu" dù file có thật, kéo theo hàng loạt "import-untyped" giả
(đã tự bắt lại bằng cách so `PYTHONPATH` bare-directory vs `pip install -e` vs `MYPYPATH` hai root
khác nhau — chỉ cách bare-directory một root khớp đúng baseline "0 lỗi" mà các task khác đã ghi).
Cài thêm gói hệ thống Qt offscreen còn thiếu (`libegl1` + bộ `libxcb-*`) — thiếu thì
`pytest-qt configure` chết ngay ở `INTERNALERROR`, không tới được bước chạy test nào.

- `ruff check`/`ruff format --check` trên toàn bộ file đổi: sạch.
- `mypy --config-file pyproject.toml --namespace-packages --explicit-package-bases src scripts`
  (chạy từ `/home/user`, `PYTHONPATH=.`): `Success: no issues found in 257 source files`.
- `pytest tests/unit/`: **3639 passed**.
- `pytest tests/integration/`: **108 passed, 4 skipped** (skip có sẵn từ trước, không liên quan).
- `pytest tests/sanity/`: **26 passed**.

Không có test nào phải nới lỏng hay bỏ qua để đạt xanh.
