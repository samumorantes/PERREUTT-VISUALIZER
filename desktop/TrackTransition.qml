import QtQuick

// Fully opaque at coverage=1. The controller owns the hold/reveal barrier.
Item {
    id: curtain
    property string phase: bridge.view.transitionPhase
    property int serial: bridge.view.transitionSerial
    property string kind: bridge.view.transitionKind
    property color tint: "#41326b"
    property string oldCover: ""
    property real coverage: phase ? 1 : 0
    property bool assetReady: nextCover.status !== Image.Loading
    visible: coverage > 0
    onSerialChanged: oldCover = bridge.view.cover
    Behavior on coverage {
        NumberAnimation {
            duration: curtain.kind === "none" ? 0 : curtain.phase ? 280 : 420
            easing.type: Easing.InOutCubic
        }
    }
    Image {
        id: nextCover
        source: bridge.view.pendingCover
        asynchronous: true; cache: true; visible: false
    }
    ShaderEffect {
        anchors.fill: parent
        visible: curtain.kind !== "vinyl" && curtain.kind !== "none"
        property real coverage: curtain.coverage
        property real progress: curtain.coverage*.5
        property real kind: curtain.kind === "tv" ? 0 : curtain.kind === "shutter" ? 1 : 2
        property color tint: curtain.tint
        fragmentShader: "shaders/transition.qsb"
    }
    Rectangle {
        anchors.fill: parent; color: "#090b10"
        visible: curtain.kind === "vinyl" || curtain.kind === "none"
        opacity: curtain.coverage
        Rectangle {
            visible: curtain.kind === "vinyl"
            anchors.centerIn: parent
            width: Math.min(parent.width,parent.height)*.65; height: width; radius: width/2
            color: "#101116"; border.color: "#45454b"; border.width: 3
            rotation: curtain.coverage*180
            Repeater {
                model: 6
                Rectangle { required property int index; anchors.centerIn: parent; width: parent.width*(.52+index*.075); height: width; radius: width/2; color: "transparent"; border.color: "#34353c" }
            }
            Image { anchors.centerIn: parent; width: parent.width*.32; height: width; source: curtain.oldCover; fillMode: Image.PreserveAspectCrop }
            Rectangle { anchors.centerIn: parent; width: 10; height: 10; radius: 5; color: "#09090b" }
        }
    }
}
