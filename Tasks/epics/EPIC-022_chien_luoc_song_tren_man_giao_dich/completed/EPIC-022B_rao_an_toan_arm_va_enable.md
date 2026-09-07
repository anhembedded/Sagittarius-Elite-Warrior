# EPIC-022B — 2 rào an toàn: chưa nạp thì không bật, đang chạy thì không đổi

**Status:** ✅ Hoàn thành (2026-09-07) · **Chặn bởi:** A · **Repo:** Elite

---

## 1. Vấn đề

**Rào 1 — bật giao dịch khi chưa có chiến lược.** Hôm nay `EnableTradingCommandHandler` không hề
biết tới khái niệm chiến lược: nó kiểm venue → kiểm kết nối → đối soát vị thế → bật. Với
`trading.live_strategy_key` rỗng (giá trị đang có trong repo), user bấm nút, UI chuyển "Trading
đang BẬT", và **không có gì chạy** — `market_tick_event_handler.py:86-91` return im lặng mỗi tick.
UI nói dối đúng nghĩa `domain-truth-rule.md`.

**Rào 2 — đổi chiến lược giữa lúc đang giao dịch.** Khi có UI đổi chiến lược (task D), đổi lúc
trading đang bật = vứt indicator state và dựng engine mới trong khi một vị thế đang mở. Chiến
lược mới không biết vị thế đó từ đâu ra; tín hiệu thoát của chiến lược cũ vĩnh viễn không tới.

## 2. Thiết kế

- `EnableTradingBlockReason` + member `NO_STRATEGY_ARMED`, kiểm **đầu tiên**, trước 2 vòng gọi
  mạng — rẻ hơn và trung thực hơn (không bắt user chờ REST rồi mới báo thiếu cấu hình).
- 2 command mới theo đúng khuôn CQRS của `enable_trading`/`disable_trading`:
  `src/application/use_cases/trading/arm_strategy/` và `.../disarm_strategy/`
  (`command.py` + `handler.py` + `result.py` + `__init__.py`).
- `ArmStrategyBlockReason`: `TRADING_IS_ENABLED`, `STRATEGY_NOT_FOUND`, `INVALID_PARAMS`,
  `MISSING_SYMBOL_OR_INTERVAL`. Validate thông số bằng chính `registry.create(key, params)` —
  `BaseStrategy.__init__` đã raise `ValueError` cho tham số không khai báo, **không viết validator
  thứ hai** (đó là nguồn sự thật thứ 2 sẽ lệch).

## 3. Đổi theo file

- `enable_trading/result.py` — thêm 1 member enum.
- `enable_trading/handler.py` — nhận thêm `LiveStrategySession`, kiểm đầu hàm.
- Mới: `arm_strategy/`, `disarm_strategy/` (4 file mỗi thư mục).
- `binance_bot_module.py` — đăng ký 2 handler vào dispatcher.
- `trading_presenter.py` — `_BLOCK_REASON_MESSAGES` thêm câu tiếng Việt cho `NO_STRATEGY_ARMED`.

## 4. Test

- `test_enable_trading.py` — thêm case: chưa arm ⇒ `block_reason == NO_STRATEGY_ARMED` **và**
  `account_reader.check_connection` **không** được gọi (chứng minh kiểm trước khi gọi mạng).
- Mới `test_arm_strategy.py` / `test_disarm_strategy.py` — 4 block reason + happy path.
