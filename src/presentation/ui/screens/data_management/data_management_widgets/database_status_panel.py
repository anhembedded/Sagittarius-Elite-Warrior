"""Embeds `DatabaseStatusTable.qml` inline in the Data Management screen's
own layout.

`EPIC-015` Phase 2: the first `QQuickWidget` in this app hosted directly on
a `kit.Panel` rather than through `QmlOverlay` (`qml/host.py`). This table
lives inside the screen's own layout — it is not a dialog — and
`QmlOverlay` wraps `Overlay` chrome (title bar, footer buttons, modality)
that an embedded table has no use for (`qml-rule.md` §0's pattern table:
neither "Modal QML" row applies here). `Panel` gives the same SURFACE
background/border the old `QFrame` + `apply_role(..., StyleRole.SURFACE)`
table card used, with no header row of its own — `DatabaseStatusTable.qml`
already renders its own header via `kit/PanelHeader`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget
from Sagittarius_Elite_Warrior.src.presentation.ui.kit import Panel, StyleRole
from Sagittarius_Elite_Warrior.src.presentation.ui.qml.DatabaseStatusTable.database_status_vm import (
    DatabaseStatusVM,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.qml.embed import QuickSurface

if TYPE_CHECKING:
    from Sagittarius_Elite_Warrior.src.presentation.ui.qml.DatabaseStatusTable.database_status_table_model import (
        DatabaseStatusTableModel,
    )

_QML = (
    Path(__file__).resolve().parents[3]
    / "qml"
    / "DatabaseStatusTable"
    / "DatabaseStatusTable.qml"
)


class DatabaseStatusPanel(Panel):
    """The Database Status table, embedded (not modal). Constructs
    `DatabaseStatusVM` around the screen's real `DatabaseStatusTableModel`
    (`DataManagementViewModel.status_model`) and re-emits its
    `rowActionRequested` so `DataManagementView` can connect the four real
    `requestInspectKlines`/`requestInspectGaps`/`requestSyncRow`/
    `requestClearRow` calls without reaching into this panel's internals.
    """

    rowActionRequested = Signal(str, str, str)  # action, symbol, interval

    def __init__(
        self,
        status_model: DatabaseStatusTableModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.body_layout.setContentsMargins(12, 12, 12, 12)
        self.body_layout.setSpacing(8)

        self._vm = DatabaseStatusVM(status_model, parent=self)
        self._vm.rowActionRequested.connect(self.rowActionRequested)
        # BUG-115: this used to be a hand-built `QQuickWidget` with a
        # transparent clear colour "so the Panel's SURFACE shows through" —
        # on a real screen the table body rendered black. `QuickSurface`
        # clears to the SURFACE token itself, through the engine factory.
        self._surface = QuickSurface(
            _QML,
            surface=StyleRole.SURFACE,
            context={"vm": self._vm},
            object_name="databaseStatusQuick",
        )
        self.body_layout.addWidget(self._surface, 1)

    def set_search_text(self, text: str) -> None:
        self._vm.setSearchText(text)

    def set_actions_enabled(self, enabled: bool) -> None:
        self._vm.setActionsEnabled(enabled)

    def set_known_shard_count(self, count: int) -> None:
        self._vm.setKnownShardCount(count)

    @property
    def root_object(self) -> QObject:
        """The loaded QML root, for tests to `findChild`/`qml_item` into by
        `objectName` — same contract `QmlOverlay.root_object` documents."""
        return self._surface.root_object
