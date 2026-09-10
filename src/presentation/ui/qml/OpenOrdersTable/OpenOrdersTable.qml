import QtQuick
import QtQuick.Layouts
import "../DataTable"

// Layout and bindings only (EPIC-015 §3.2), renders `OpenOrdersVM.rows`.
// Header + row-list + empty-state skeleton is `DataTable` (`BOT-124`).
ColumnLayout {
    id: root
    objectName: "openOrdersTableBody"
    spacing: 10

    readonly property int timeColumnWidth: 150
    readonly property int symbolColumnWidth: 110
    readonly property int sideColumnWidth: 70
    readonly property int typeColumnWidth: 130
    readonly property int quantityColumnWidth: 120
    readonly property int priceColumnWidth: 130
    readonly property int cancelColumnWidth: 70

    DataTable {
        Layout.fillWidth: true
        Layout.fillHeight: true
        listObjectName: "openOrdersRows"
        emptyObjectName: "lblOpenOrdersEmpty"
        headerLetterSpacing: 0.5
        reuseItems: true
        columns: [
            { key: "time", label: "TIME", width: root.timeColumnWidth },
            { key: "symbol", label: "SYMBOL", width: root.symbolColumnWidth },
            { key: "side", label: "SIDE", width: root.sideColumnWidth },
            { key: "type", label: "ORDER TYPE", width: root.typeColumnWidth },
            { key: "quantity", label: "QUANTITY", width: root.quantityColumnWidth, align: "right" },
            { key: "price", label: "PRICE", width: root.priceColumnWidth, align: "right" },
            { key: "status", label: "STATUS", fillWidth: true, align: "right" },
            { key: "cancel", label: "", width: root.cancelColumnWidth, align: "right" },
        ]
        rowsModel: vm ? vm.rows : null
        isEmpty: vm ? vm.rows.length === 0 : false
        emptyText: "No open orders pending"
        rowDelegate: Component {
            OpenOrderRow {
                width: ListView.view.width
                timeWidth: root.timeColumnWidth
                symbolWidth: root.symbolColumnWidth
                sideWidth: root.sideColumnWidth
                typeWidth: root.typeColumnWidth
                quantityWidth: root.quantityColumnWidth
                priceWidth: root.priceColumnWidth
                cancelWidth: root.cancelColumnWidth
            }
        }
    }
}
