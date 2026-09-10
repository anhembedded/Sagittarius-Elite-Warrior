"""Standalone live preview for the DatabaseStatusTable QML component.

Seeds the real `DatabaseStatusTableModel` via its own `upsert_row()` — the
same two example shards the mockup shows — rather than fabricating a
second data shape (see NOTES.md).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget
from Sagittarius_Elite_Warrior.src.presentation.ui.kit import StyleRole
from Sagittarius_Elite_Warrior.src.presentation.ui.qml.DatabaseStatusTable.database_status_table_model import (
    DatabaseStatusTableModel,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.qml.DatabaseStatusTable.database_status_vm import (
    DatabaseStatusVM,
)
from Sagittarius_Elite_Warrior.src.presentation.ui.qml.embed import QuickSurface

_QML_FILE = Path(__file__).with_name("DatabaseStatusTable.qml")


def build_preview() -> QWidget:
    """Builds the table body with two example shards, no host chrome."""
    model = DatabaseStatusTableModel()
    model.upsert_row(
        symbol="BTCUSDT",
        first_record="2026-07-23 15:41:05",
        last_record="2026-08-26 01:19:21",
        total_candles="2,885,897",
        status_text="OK",
        interval="1s",
    )
    model.upsert_row(
        symbol="BTCUSDT",
        first_record="2026-07-27 07:30:00",
        last_record="2026-08-26 07:00:00",
        total_candles="1,440",
        status_text="OK",
        interval="30m",
    )
    vm = DatabaseStatusVM(model)

    surface = QuickSurface(
        _QML_FILE,
        surface=StyleRole.SURFACE,
        context={"vm": vm, "model": model},
        object_name="databaseStatusTablePreview",
    )
    surface.resize(900, 260)
    return surface
