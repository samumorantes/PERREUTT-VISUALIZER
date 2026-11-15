import QtQuick
import QtQuick.Controls
Button {
    id: control
    hoverEnabled: true
    implicitHeight: 38
    implicitWidth: Math.max(42, contentItem.implicitWidth + 28)
    contentItem: Text {
        text: control.text; color: "#f0f2fb"; font.pixelSize: 13; font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: 12
        color: control.down ? "#405c687d" : control.hovered ? "#404d6076" : "#80313b4e"
        border.width: 1; border.color: control.activeFocus ? "#98e7ce" : "#40dce5ff"
    }
}
