"""Standalone live preview for the shared `DataTable` QML component (BOT-124).

Demonstrates the component in isolation with a trivial two-column row
delegate — not a real table's row shape, since `DataTable` has no opinion
on what a row looks like (BOT-124 §5). The three real callers
(`TradeLogTable`/`KlineInspectorTable`/`DatabaseStatusTable`) each keep
their own `preview.py` showing their real row delegate.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget
from Sagittarius_Elite_Warrior.src.presentation.ui.kit import StyleRole
from Sagittarius_Elite_Warrior.src.presentation.ui.qml.embed import QuickSurface

_QML_FILE = Path(__file__).with_name("_DataTablePreview.qml")


def build_preview() -> QWidget:
    """Builds the DataTable preview, no host chrome."""
    surface = QuickSurface(
        _QML_FILE,
        surface=StyleRole.SURFACE,
        object_name="dataTablePreview",
    )
    surface.resize(640, 360)
    return surface
