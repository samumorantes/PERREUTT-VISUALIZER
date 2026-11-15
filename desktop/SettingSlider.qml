import QtQuick
import QtQuick.Controls
Column {
    property string label
    property string settingKey
    property real minimum: 0
    property real maximum: 100
    property real increment: 1
    property real current: bridge.settings[settingKey] || 0
    width: parent.width; spacing: 4
    Row {
        width: parent.width
        Label { width: parent.width - 48; text: label; color: "#dce5f3"; font.pixelSize: 12; wrapMode: Text.Wrap }
        Label { width: 48; text: Math.round(current * 100) / 100; color: "#a0ebd3"; font.pixelSize: 12; horizontalAlignment: Text.AlignRight }
    }
    Slider {
        id: control
        width: parent.width; from: minimum; to: maximum; stepSize: increment; value: current
        implicitHeight: 28
        onMoved: bridge.setSetting(settingKey, value)
        background: Rectangle {
            x: control.leftPadding; y: (control.height-height)/2; width: control.availableWidth; height: 4; radius: 2
            color: "#32e1eaff"
            Rectangle { width: control.visualPosition * parent.width; height: parent.height; radius: 2; color: "#84ddc3" }
        }
        handle: Rectangle {
            x: control.leftPadding + control.visualPosition * (control.availableWidth-width)
            y: (control.height-height)/2; width: 16; height: 16; radius: 8
            color: control.pressed ? "#8de5c9" : "#eef8ff"; border.color: "#909ce9d1"
        }
    }
}
