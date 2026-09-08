import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Shared header + row-list + empty-state skeleton for every `qml/` table
// widget (`BOT-124`) — extracted from three near-identical copies
// (`TradeLogTable`, `KlineInspectorTable`, `DatabaseStatusTable`), each of
// which repeated the same root `ColumnLayout` -> header `RowLayout` ->
// divider `Rectangle` -> `ListView` -> empty `Text` skeleton, differing
// only in column widths/labels, model, row delegate, and empty-state copy
// (qml-rule.md §0.2; see this widget's own NOTES.md for the extraction).
//
// Deliberately does NOT own anything specific to one table: no filter tabs
// (`TradeLogTable`), no subtitle line (`KlineInspectorTable`), no search
// field or row actions (`DatabaseStatusTable`) — those stay in each
// caller's own `.qml` file, composed alongside `DataTable` rather than
// folded into it (BOT-124 §5). `DataTable` owns only the frame every table
// shares.
//
// Column widths stay a Single Source of Truth per column
// (ui-presentation-rule.md): each column descriptor's `width` is read by
// this component's header `Repeater`, and independently by whatever
// `rowDelegate` the caller supplies — the caller defines its own
// `readonly property int xColumnWidth` and passes the SAME value into
// both the matching `columns` entry and its row delegate's own width
// property, exactly as each of the three original tables already did for
// their own header/row pair.
ColumnLayout {
    id: root
    spacing: 10

    //: Header column descriptors, left to right. Each entry:
    //: `{ key: string (optional, used only to build a header-cell
    //:   objectName), label: string, width: int (omit for a fillWidth
    //:   column), fillWidth: bool (default false),
    //:   align: "left"|"right" (default "left") }`.
    //: DataTable never reads row data itself — `key` exists purely so a
    //: header cell can be found by name in a test.
    property var columns: []

    //: Passed straight through to the internal `ListView.model` — a plain
    //: list (`TradeLogVM`/`KlineInspectorVM` style) or a real
    //: `QAbstractListModel` (`DatabaseStatusTableModel` style) both work
    //: unchanged, exactly as the three original tables relied on.
    property var rowsModel: null

    //: The row `Component` the internal `ListView` instantiates. Defined
    //: in the CALLER's own `.qml` file (never here — `DataTable` stays
    //: ignorant of what a row looks like), so it closes over that file's
    //: own column-width properties. A row delegate sizes itself with the
    //: `ListView.view.width` attached property rather than an `id`
    //: reference into this file — the attachment happens at
    //: instantiation time, so it resolves correctly regardless of which
    //: `.qml` file the `Component` body is written in.
    property Component rowDelegate: null

    //: Whether to show the empty-state message. A plain bool, not derived
    //: here, because "empty" means something different per caller
    //: (`vm.rows.length === 0` vs. a null-guarded `vm.rowCount === 0`).
    property bool isEmpty: false
    property string emptyText: ""

    //: Every original table set these explicitly (or relied on Qt's own
    //: `ListView` default), so callers keep setting them explicitly here
    //: too, rather than a new caller silently inheriting a default it
    //: never chose.
    property bool reuseItems: false
    property real rowSpacing: 0

    //: Table-wide, not per-column — all three original tables used one
    //: `letterSpacing` value across their whole header row, never a
    //: per-column one.
    property real headerLetterSpacing: 0

    //: `objectName` for the internal `ListView`/empty `Text` — kept
    //: settable so a migrated table preserves its own exact
    //: pre-extraction name (nothing currently asserts on either, but a
    //: silent rename is still an avoidable behavior change).
    property string listObjectName: "dataTableRows"
    property string emptyObjectName: "dataTableEmpty"

    //: `BOT-128` — the width the declared columns actually need. A table
    //: whose columns are narrower than the box simply fills it; one whose
    //: columns need more makes the `Flickable` below scroll instead of
    //: dropping the columns that did not fit.
    //:
    //: Why sum the declared widths rather than let the header `RowLayout`
    //: compress: those widths are a Single Source of Truth shared with each
    //: caller's row delegate (see the note at the top). Compressing the
    //: header without compressing the rows misaligns the two, which is why
    //: the header cells below no longer shrink below what they declared.
    readonly property real requiredWidth: {
        var total = 0
        for (var i = 0; i < columns.length; ++i) {
            var declared = columns[i].width
            total += declared !== undefined ? declared : root.fillColumnMinimumWidth
        }
        return columns.length > 0
            ? total + (columns.length - 1) * root.headerSpacing
            : 0
    }

    //: Space between header cells, and the same value the content width
    //: above accounts for — one constant rather than an `8` in two places
    //: that can drift apart.
    readonly property real headerSpacing: 8

    //: What a `fillWidth` column is assumed to need when the table is at
    //: its scrolling minimum. `fillWidth` columns have no declared width by
    //: definition, and a column of zero width is not a column.
    readonly property real fillColumnMinimumWidth: 80

    Flickable {
        id: scroller
        objectName: "dataTableScroller"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        //: Never narrower than the box: a table that fits must look exactly
        //: as it did before this wrapper existed.
        contentWidth: Math.max(width, root.requiredWidth)
        contentHeight: height
        flickableDirection: Flickable.HorizontalFlick
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.horizontal: ScrollBar {
            objectName: "dataTableHorizontalScrollBar"
            //: Only present when there is something to scroll to, so a
            //: table that fits does not grow a permanent empty bar.
            policy: scroller.contentWidth > scroller.width
                ? ScrollBar.AlwaysOn
                : ScrollBar.AlwaysOff
        }

        ColumnLayout {
            id: content
            width: scroller.contentWidth
            height: scroller.height
            spacing: root.spacing

            RowLayout {
                Layout.fillWidth: true
                spacing: root.headerSpacing

            Repeater {
                model: root.columns
                delegate: Text {
                    objectName: "dataTableHeaderCell_" + (modelData.key !== undefined ? modelData.key : index)
                    Layout.preferredWidth: modelData.width !== undefined ? modelData.width : -1
                    Layout.fillWidth: !!modelData.fillWidth
                    // `elide` stays for the `fillWidth` column, which is still
                    // the one column that can be squeezed (BUG-076: without it a
                    // shrunken `Text` keeps painting its full un-elided glyphs
                    // over whatever sits to its right — measured at 16px of
                    // overflow into the next column).
                    //
                    // `BOT-128` changed the other half: a declared-width column
                    // no longer shrinks below what it declared. It used to carry
                    // `Layout.minimumWidth: 0`, which let a narrow box compress
                    // every column — and since each width is shared with the
                    // caller's row delegate, which did NOT compress, the header
                    // and its rows drifted out of alignment and the columns that
                    // did not fit were simply lost off the edge. The `Flickable`
                    // above scrolls to them instead.
                    Layout.minimumWidth: modelData.width !== undefined
                        ? modelData.width
                        : 0
                    elide: Text.ElideRight
                    horizontalAlignment: modelData.align === "right" ? Text.AlignRight : Text.AlignLeft
                    text: modelData.label
                    textFormat: Text.PlainText
                    color: Theme.muted
                    font.pixelSize: 10
                    font.letterSpacing: root.headerLetterSpacing
                }
            }
        }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }

            ListView {
                id: rowsView
                objectName: root.listObjectName
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                reuseItems: root.reuseItems
                spacing: root.rowSpacing
                model: root.rowsModel
                delegate: root.rowDelegate
            }

            Text {
                objectName: root.emptyObjectName
                Layout.fillWidth: true
                Layout.topMargin: 12
                visible: root.isEmpty
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: root.emptyText
                textFormat: Text.PlainText
                color: Theme.muted
                font.pixelSize: 11
            }
        }
    }
}
