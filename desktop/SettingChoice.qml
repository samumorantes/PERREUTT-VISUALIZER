import QtQuick
import QtQuick.Controls
Column {
    property string label
    property string settingKey
    property var labels: []
    property var values: []
    property var current: bridge.settings[settingKey]
    width: parent.width; spacing: 5
    Label { width: parent.width; text: label; color: "#dce5f3"; font.pixelSize: 12; wrapMode: Text.Wrap }
    ComboBox {
        id: control
        width: parent.width; model: labels; implicitHeight: 40
        leftPadding: 12; rightPadding: 30; font.pixelSize: 13
        currentIndex: Math.max(0, values.indexOf(current))
        onActivated: bridge.setSetting(settingKey, values[currentIndex])
        background: Rectangle { radius: 10; color: control.hovered ? "#30c3d3ec" : "#18ffffff"; border.color: control.activeFocus ? "#89e6c8" : "#32d7e3ff" }
        contentItem: Text { text: control.displayText; font: control.font; color: "#f0f4fc"; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter }
        indicator: Text { x: control.width-24; y: (control.height-height)/2; text: "⌄"; color: "#ced9ed"; font.pixelSize: 16 }
        delegate: ItemDelegate {
            width: control.width; height: 38
            contentItem: Text { text: modelData; color: "#eef3fb"; font.pixelSize: 13; verticalAlignment: Text.AlignVCenter }
            highlighted: control.highlightedIndex === index
            background: Rectangle { radius: 7; color: highlighted ? "#39554f" : "transparent" }
        }
        popup: Popup {
            y: control.height + 4; width: control.width; padding: 5
            implicitHeight: Math.min(contentItem.implicitHeight + 10, 280)
            contentItem: ListView { clip: true; implicitHeight: contentHeight; model: control.popup.visible ? control.delegateModel : null; currentIndex: control.highlightedIndex; ScrollIndicator.vertical: ScrollIndicator {} }
            background: Rectangle { radius: 12; color: "#f0202938"; border.color: "#50667b92" }
        }
    }
}
