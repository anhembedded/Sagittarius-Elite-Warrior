"""`BOT-128` — a table whose columns need more width than the box gets must
scroll to them, not lose them.

The reported defect: on the Trading screen the two tables sit side by side, so
each got ~390px while its declared columns need 838-896px. Every column past
the third simply was not there — and it could not be reached, because the
header cells carried `Layout.minimumWidth: 0`, so the `RowLayout` compressed
what it could and dropped the rest off the edge with no scroll bar.

These load `DataTable.qml` directly, at a width narrower than its own columns,
because that is the condition the defect needs and the one no screen test
reproduces on purpose.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQuickWidgets import QQuickWidget
from Sagittarius_Elite_Warrior.src.presentation.ui import qml as qml_package
from Sagittarius_Elite_Warrior.tests.conftest import find_qml_item

#: Resolved off the package rather than a path literal, so moving the QML tree
#: breaks the import instead of silently loading nothing.
_DATA_TABLE_QML = Path(qml_package.__file__).parent / "DataTable" / "DataTable.qml"

#: Four columns of 200px plus the header spacing — comfortably more than the
#: narrow box below, and comfortably less than the wide one.
_COLUMN_WIDTH = 200
_COLUMN_COUNT = 4
_NARROW_BOX = 300
_WIDE_BOX = 1400


def _table(qapp, box_width: int) -> QQuickWidget:
    widget = QQuickWidget()
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.setSource(QUrl.fromLocalFile(str(_DATA_TABLE_QML)))
    assert widget.status() is QQuickWidget.Status.Ready, widget.errors()
    widget.rootObject().setProperty(
        "columns",
        [
            {"key": f"c{index}", "label": f"COLUMN {index}", "width": _COLUMN_WIDTH}
            for index in range(_COLUMN_COUNT)
        ],
    )
    widget.resize(box_width, 300)
    widget.show()
    qapp.processEvents()
    return widget


def _scroller(widget: QQuickWidget):
    return find_qml_item(widget.rootObject(), "dataTableScroller")


def test_a_narrow_box_scrolls_to_the_columns_it_cannot_show(qapp):
    # The widget is held in a local on purpose: dropping the last Python
    # reference deletes the underlying C++ object, and every property read
    # below then raises instead of failing on its value.
    widget = _table(qapp, _NARROW_BOX)
    scroller = _scroller(widget)

    assert scroller.property("contentWidth") > scroller.property("width")


def test_the_scrollable_width_covers_every_declared_column(qapp):
    """Not merely "wider than the box" — wide enough that the last column is
    actually reachable. A content width that stopped short would hide the same
    columns, just with a scroll bar in front of them."""
    widget = _table(qapp, _NARROW_BOX)
    scroller = _scroller(widget)

    assert scroller.property("contentWidth") >= _COLUMN_WIDTH * _COLUMN_COUNT


def test_a_wide_box_is_left_exactly_as_it_was(qapp):
    """The other half: a table that fits must behave as it did before this
    wrapper existed — no scrolling, content the full width of the box."""
    widget = _table(qapp, _WIDE_BOX)
    scroller = _scroller(widget)

    assert scroller.property("contentWidth") == scroller.property("width")


def test_the_scroll_bar_reports_how_much_of_the_table_is_visible(qapp):
    """`size` is the fraction of the content the box shows: below 1 when there
    are columns off-screen to reach, exactly 1 when there are none.

    Asserted on `size` rather than on `policy`: the policy is a QML-side enum
    that has no Python converter, so reading it raises instead of comparing —
    and a test that cannot read the value it claims to check is no test."""
    narrow_widget = _table(qapp, _NARROW_BOX)
    wide_widget = _table(qapp, _WIDE_BOX)
    narrow = find_qml_item(narrow_widget.rootObject(), "dataTableHorizontalScrollBar")
    wide = find_qml_item(wide_widget.rootObject(), "dataTableHorizontalScrollBar")

    assert narrow.property("size") < 1.0
    assert wide.property("size") == 1.0


def test_a_declared_column_is_not_compressed_to_fit(qapp):
    """The root cause, pinned. Header cells used to carry
    `Layout.minimumWidth: 0`, which let the row compress every column — and
    since each width is shared with the caller's row delegate, which did not
    compress, the header and its rows drifted apart."""
    widget = _table(qapp, _NARROW_BOX)
    first_cell = find_qml_item(widget.rootObject(), "dataTableHeaderCell_c0")

    assert first_cell.property("width") == _COLUMN_WIDTH
