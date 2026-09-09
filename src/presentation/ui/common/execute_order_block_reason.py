"""`EPIC-024B` — human-readable text for `ExecuteOrderResult.blocked_by`/
`CancelOrderResult.blocked_by`, shared by `DashboardPresenter` and
`TradingPresenter` (`architecture-rule.md` §5 / `test_no_cross_screen_
imports.py` — a screen-to-screen import is forbidden, so this lives here,
not in either screen's own presenter module).
"""

from __future__ import annotations

from Sagittarius_Elite_Warrior.src.application.use_cases.trading.execute_order.result import (
    ExecuteOrderNotionalRejection,
    ExecuteOrderSafetyGate,
)
from Sagittarius_Elite_Warrior.src.domain.trading.policies.trading_limit_policy import (
    TradingLimitViolation,
)
from Sagittarius_Elite_Warrior.src.presentation.enum_labels import EnumLabels

#: `ExecuteOrderResult.blocked_by`/`CancelOrderResult.blocked_by` share
#: `ExecuteOrderSafetyGate` — one table covers the manual order card and
#: the Open Orders "Huỷ" button, on both screens.
_SAFETY_GATE_MESSAGES = EnumLabels(
    ExecuteOrderSafetyGate,
    {
        ExecuteOrderSafetyGate.TRADING_VENUE_DISABLED: (
            "Trading venue đang tắt trong cấu hình — chỉ hỗ trợ Futures Testnet."
        ),
        ExecuteOrderSafetyGate.TRADING_SWITCH_OFF: (
            "Giao dịch đang TẮT — bật giao dịch trước khi đặt/huỷ lệnh."
        ),
        ExecuteOrderSafetyGate.CONNECTION_NOT_READY: (
            "Kết nối tới sàn chưa sẵn sàng — kiểm tra lại API key/kết nối mạng."
        ),
    },
)

_LIMIT_VIOLATION_MESSAGES = EnumLabels(
    TradingLimitViolation,
    {
        TradingLimitViolation.MAX_ORDERS_PER_SESSION: (
            "Đã đạt số lệnh tối đa cho phép trong phiên này."
        ),
        TradingLimitViolation.MAX_NOTIONAL_PER_ORDER: (
            "Giá trị lệnh vượt trần cho phép mỗi lệnh."
        ),
        TradingLimitViolation.MAX_POSITIONS_PER_SYMBOL: (
            "Symbol này đang có vị thế mở — không mở thêm."
        ),
        TradingLimitViolation.MIN_ORDER_INTERVAL: (
            "Lệnh gửi quá gần lệnh trước trên cùng symbol."
        ),
    },
)


def format_execute_order_block_reason(
    blocked_by: ExecuteOrderSafetyGate
    | ExecuteOrderNotionalRejection
    | TradingLimitViolation
    | None,
) -> str:
    """@brief Human message for any member of `ExecuteOrderResult.
    blocked_by`'s union — the manual order card needs all three kinds
    (`trade_once_formatter.py`'s CLI-only counterpart never had to)."""
    if isinstance(blocked_by, ExecuteOrderSafetyGate):
        return _SAFETY_GATE_MESSAGES[blocked_by]
    if isinstance(blocked_by, TradingLimitViolation):
        return _LIMIT_VIOLATION_MESSAGES[blocked_by]
    if blocked_by is ExecuteOrderNotionalRejection.MIN_NOTIONAL:
        return "Giá trị lệnh (sau khi làm tròn) chưa đạt notional tối thiểu của symbol."
    return "Không rõ lý do."  # pragma: no cover - blocked_by is None handled by callers first
