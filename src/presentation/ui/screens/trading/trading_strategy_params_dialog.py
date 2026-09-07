"""`EPIC-022D` — the Trading screen's "Thông số Chiến lược" dialog.

@details One tab, not the Backtest dialog's four. Backtest's extra tabs
carry broker properties (commission, slippage, the simulated fill model)
and a placeholder style tab; on the Trading screen orders fill on the real
exchange, so there is no fill model to configure, and sizing/leverage — the
two things a live trader does set — live on the strategy card itself where
they are visible without opening a dialog. Showing empty or inapplicable
tabs here would be `domain-truth-rule.md`'s "do not present an unsupported
capability as available", one dialog down.

The fields themselves are `BotParamFieldWidget`, the same widget the
Backtest dialog renders, from the same schema built by the same
`build_bot_params_schema()` — so a strategy's parameters look and validate
identically wherever they are edited.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.assets import Palette
from Sagittarius_Elite_Warrior.src.presentation.ui.components.strategy_params import (
    BotParamFieldWidget,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.kit import (
    Overlay,
    StyledButton,
    StyleRole,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QHBoxLayout

    from .trading_view_model import TradingViewModel

_TITLE = "Thông số Chiến lược"
_EMPTY_TEXT = "Chiến lược này không khai báo thông số nào."
_SAVE_TEXT = "Lưu"
_CANCEL_TEXT = "Huỷ"


class TradingStrategyParamsDialog(Overlay):
    """@brief Edits the selected strategy's declared parameters."""

    def __init__(
        self, view_model: TradingViewModel, parent: QWidget | None = None
    ) -> None:
        super().__init__(_TITLE, parent=parent)
        self.setObjectName("tradingStrategyParamsDialog")
        self._vm = view_model
        self._field_widgets: list[BotParamFieldWidget] = []
        self.resize(520, 560)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setObjectName("strategyParamsContent")
        self._content_layout.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self._content)
        self.body_layout.addWidget(scroll)

        self._error_label = QLabel()
        self._error_label.setObjectName("lblStrategyParamsError")
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(f"color: {Palette.DANGER}; font-size: 11px;")
        self._error_label.setVisible(False)
        self.body_layout.addWidget(self._error_label)

        self._vm.botParamsChanged.connect(self._sync_from_view_model)
        self._sync_from_view_model()

    def _build_buttons(self) -> QHBoxLayout:
        from PySide6.QtWidgets import QHBoxLayout as _QHBoxLayout

        row = _QHBoxLayout()
        self._cancel_button = StyledButton(
            _CANCEL_TEXT, role=StyleRole.SECONDARY_BUTTON
        )
        self._cancel_button.setObjectName("btnStrategyParamsCancel")
        self._cancel_button.clicked.connect(self.reject)
        self._save_button = StyledButton(_SAVE_TEXT, role=StyleRole.PRIMARY_BUTTON)
        self._save_button.setObjectName("btnStrategyParamsSave")
        self._save_button.clicked.connect(self._on_save_clicked)
        row.addStretch(1)
        row.addWidget(self._cancel_button)
        row.addWidget(self._save_button)
        return row

    def collect_values(self) -> dict[str, Any]:
        """@brief What the user typed, keyed by parameter name."""
        return {
            widget.field_name: widget.value()
            for widget in self._field_widgets
            if widget.field_name
        }

    def _on_save_clicked(self) -> None:
        """@details Asks the ViewModel to save and closes only if it
        accepted. Staying open on a rejection is the point: the error
        label is inside this dialog, and closing over an invalid value
        would leave the user with a card that quietly kept the old
        parameters while they believed they had changed them."""
        self._vm.requestBotParamsSave(self.collect_values())
        if not self._vm.botParamsError:
            self.accept()

    def _sync_from_view_model(self) -> None:
        self._error_label.setText(self._vm.botParamsError)
        self._error_label.setVisible(bool(self._vm.botParamsError))
        self._rebuild_fields(self._vm.botParamsRows)

    def _rebuild_fields(self, rows: list[dict]) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self._field_widgets = []

        if not rows:
            empty = QLabel(_EMPTY_TEXT)
            empty.setStyleSheet(f"color: {Palette.MUTED}; font-size: 11px;")
            self._content_layout.addWidget(empty)
            self._content_layout.addStretch(1)
            return

        for row in rows:
            if row.get("rowType") == "header":
                header = QLabel(str(row.get("groupLabel", "")))
                header.setStyleSheet(
                    f"color: {Palette.TEXT_PRIMARY}; font-size: 12px; font-weight: 600;"
                )
                self._content_layout.addWidget(header)
                continue
            field_widget = BotParamFieldWidget(dict(row.get("field", {})), self._vm)
            self._field_widgets.append(field_widget)
            self._content_layout.addWidget(field_widget)
        self._content_layout.addStretch(1)
