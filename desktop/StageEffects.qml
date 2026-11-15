import QtQuick

Item {
    id: fx
    required property real seconds
    required property real pulseAge
    required property color pulseColor
    required property bool chill
    property real dropStart: -100
    property real dropAge: seconds-dropStart
    property string transitionKind: "none"
    property real transitionStart: -100
    property real transitionDuration: transitionKind === "tv" ? .7 : transitionKind === "shutter" ? 1.15 : transitionKind === "vinyl" ? 1.25 : .95
    property real progress: (seconds-transitionStart)/transitionDuration
    function burst() { if (bridge.settings.dropFx && !bridge.settings.reducedMotion) dropStart=seconds }
    function transition(kind) { transitionKind=kind; transitionStart=seconds }
    function clear() { dropStart=-100; transitionStart=-100 }
    Row {
        anchors.horizontalCenter: parent.horizontalCenter; y: parent.height*.72
        height: parent.height*.19; spacing: 3
        visible: bridge.settings.spectrum && !fx.chill
        Repeater {
            model: 24
            Rectangle {
                required property int index
                width: (fx.width*.8-69)/24
                height: parent.height*(.1+.9*Math.max(0,1-fx.pulseAge/.5)*(.25+.75*Math.abs(Math.sin(index*1.7+fx.seconds*2))))
                anchors.bottom: parent.bottom; radius: 2
                color: fx.pulseColor; opacity: .4
            }
        }
    }
    Repeater {
        model: bridge.settings.dropFx && fx.dropAge >= 0 && fx.dropAge < 1.4 && !bridge.settings.reducedMotion ? (bridge.view.qualityScale < .8 ? 24 : 60) : 0
        Rectangle {
            required property int index
            property real angle: index*2.39996
            property real speed: .2+(index%7)*.035
            width: 4+index%5; height: width*.55; radius: 1
            x: fx.width*(.5+Math.cos(angle)*speed*fx.dropAge)
            y: fx.height*(.5+Math.sin(angle)*speed*fx.dropAge+.18*fx.dropAge*fx.dropAge)
            rotation: index*17+fx.dropAge*150; opacity: Math.max(0,1-fx.dropAge/1.4)
            color: index%3 ? fx.pulseColor : "white"
        }
    }
    ShaderEffect {
        anchors.fill: parent
        visible: fx.transitionKind !== "none" && fx.transitionKind !== "vinyl" && fx.progress >= 0 && fx.progress < 1 && !bridge.settings.reducedMotion
        property real progress: Math.max(0,Math.min(1,fx.progress))
        property real coverage: Math.sin(progress*Math.PI)
        property real kind: fx.transitionKind === "tv" ? 0 : fx.transitionKind === "shutter" ? 1 : 2
        property color tint: fx.pulseColor
        fragmentShader: "shaders/transition.qsb"
    }
    Rectangle {
        visible: fx.transitionKind === "vinyl" && fx.progress >= 0 && fx.progress < 1 && !bridge.settings.reducedMotion
        anchors.fill: parent; color: "#e5090b10"
        opacity: Math.sin(Math.max(0,Math.min(1,fx.progress))*Math.PI)
        Rectangle {
            anchors.centerIn: parent; width: Math.min(parent.width,parent.height)*.7; height: width; radius: width/2
            color: "#101116"; border.color: "#45454b"; border.width: 3
            rotation: fx.progress*360
            Repeater {
                model: 6
                Rectangle { required property int index; anchors.centerIn: parent; width: parent.width*(.52+index*.075); height: width; radius: width/2; color: "transparent"; border.color: "#34353c" }
            }
            Image { anchors.centerIn: parent; width: parent.width*.32; height: width; source: bridge.view.cover; fillMode: Image.PreserveAspectCrop }
            Rectangle { anchors.centerIn: parent; width: 10; height: 10; radius: 5; color: "#09090b" }
        }
    }
}
