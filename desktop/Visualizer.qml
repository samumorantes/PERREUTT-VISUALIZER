import QtQuick
import QtQuick.Controls
import QtQuick.Window

ApplicationWindow {
    id: win
    width: 1280; height: 850; minimumWidth: 640; minimumHeight: 420
    visible: true; color: "#08090b"
    property bool translationDisplay: false
    property string displayId: translationDisplay ? "translation" : "main"
    property bool qualityReporter: false
    property real seconds: 0
    property real positionSampleTime: 0
    property real songPosition: bridge.position
    property real pulseStart: -100
    property real pulseDuration: .47
    property color pulseColor: "#ff1744"
    property bool uiAwake: true
    property int frames: 0
    property int fpsFrames: 0
    property real fpsTime: 0
    property bool rendering: visible && visibility !== Window.Minimized
    property bool motion: !bridge.settings.reducedMotion
    property string egg: translationDisplay ? "" : bridge.lyric.egg
    property bool eggWhite: egg === "eoo" && motion && Math.floor(Math.max(0,songPosition-bridge.lyric.start)/.9)%2 === 1
    property real pulseAge: seconds-pulseStart
    property real pulseLevel: Math.max(0,1-pulseAge/Math.max(.01,pulseDuration))
    property real desiredSize: Math.max(24,scene.width*bridge.settings.fontSize/100)
    property string lyricFont: egg ? "Impact" : ({arcade:arcadeFamily,grotesk:groteskFamily,impact:"Impact",courier:"Courier New",georgia:"Georgia",system:"Segoe UI"})[bridge.settings.font]
    property real lyricSize: {
        var words = bridge.lyric.groups, longest=1, total=0
        for (var i=0;i<words.length;i++) {
            var text=""
            for(var j=0;j<words[i].syllables.length;j++) text+=words[i].syllables[j].text
            var w=measure.advanceWidth(displayText(text))
            longest=Math.max(longest,w); total+=w
        }
        return Math.min(desiredSize,desiredSize*(scene.width*.78)/longest,desiredSize*(scene.width*1.5)/Math.max(1,total),scene.height*.17)
    }
    property color lyricColor: egg ? (eggWhite ? "#000000" : "#ffffff") : "#ffffff"
    property color topColor: "#ffffff"
    property color bottomColor: "#ffffff"
    FontMetrics { id: measure; font.family: win.lyricFont; font.pixelSize: win.desiredSize }
    function displayText(text) { return bridge.settings.upper ? text.toUpperCase() : text }
    function toggleMode() { bridge.setSetting("mood",bridge.view.chill ? "party" : "chill") }
    function toggleQR() { bridge.setSetting("qrEnabled",!bridge.settings.qrEnabled) }
    function contrastAt(x,y,previous) {
        if (!bridge.view.chill || egg) return eggWhite ? "#000000" : "#ffffff"
        var pX=(x-.5)*3, pY=(y-.5)*3, t=(motion ? seconds : 0)*.18
        var f=(Math.sin(pX*2+Math.sin(pY*2+t))+.1)/2+.45
        var style=bridge.settings.fluidStyle
        if(style===1) f=(Math.sin(Math.atan2(pY,pX)*3+Math.sqrt(pX*pX+pY*pY)*4-t)+1)/2
        if(style===2) f=(Math.sin(pX*3+t)+Math.sin(pY*4-t)+Math.sin(Math.sqrt(pX*pX+pY*pY)*4-t))/6+.5
        if(style===3) f=Math.pow(Math.max(0,Math.sin(pX*2+Math.sin(pY+t)+t)),2)*(.4+.6*y)
        var band=Math.max(0,Math.min(3.999,f*4)), i=Math.floor(band), u=band-i; u=u*u*(3-2*u)
        var a=Qt.color(bridge.view.palette[i]), b=Qt.color(bridge.view.palette[i+1])
        var light=((a.r*(1-u)+b.r*u)*.2126+(a.g*(1-u)+b.g*u)*.7152+(a.b*(1-u)+b.b*u)*.0722)*(.85+.15*Math.sin(pX+pY+t))
        return light>.52 ? "#111111" : light<.38 ? "#ffffff" : previous
    }
    title: translationDisplay ? "FIESTA · Traducción" : "FIESTA · Nativo"
    palette.window: "#171a22"; palette.windowText: "#ffffff"; palette.text: "#ffffff"
    palette.base: "#252a36"; palette.button: "#303747"; palette.buttonText: "#ffffff"
    palette.highlight: "#28c98a"; palette.highlightedText: "#101820"

    function openSettings() { settingsDrawer.open() }
    function wake() { uiAwake = true; hideUI.restart() }
    function toggleFullscreen() { visibility = visibility === Window.FullScreen ? Window.Windowed : Window.FullScreen }
    onFrameSwapped: {
        if (win.rendering && trackCurtain.coverage >= 1 && trackCurtain.assetReady && bridge.view.transitionPhase)
            bridge.transitionFrame(displayId, bridge.view.transitionSerial, bridge.view.transitionPhase)
    }
    FrameAnimation {
        running: win.rendering
        onTriggered: {
            win.seconds += Math.min(frameTime, .1)
            win.frames++
            win.fpsFrames++; win.fpsTime+=frameTime
            if(win.fpsTime>=1) {
                if(win.qualityReporter) bridge.reportFps(win.fpsFrames/win.fpsTime)
                win.fpsFrames=0; win.fpsTime=0
            }
            win.songPosition = bridge.position + (bridge.view.playing ? Math.min(.2, win.seconds - win.positionSampleTime) : 0)
        }
    }
    Connections {
        target: bridge
        function onPositionChanged() { win.positionSampleTime = win.seconds; win.songPosition = bridge.position }
        function onPulse(age, duration, color, drop) { win.pulseStart = win.seconds - age; win.pulseDuration = duration; win.pulseColor = color; if(drop) stageFx.burst() }
        function onClearPulse() { win.pulseStart = -100; stageFx.clear() }
        function onTransitionRequested(kind) { stageFx.transition(kind) }
        function onDropRequested() { stageFx.burst() }
    }
    Timer { interval: 180; repeat: true; running: win.rendering; onTriggered: { win.lyricColor=win.contrastAt(.5,.5,win.lyricColor); win.topColor=bridge.settings.smartContrast ? win.contrastAt(.25,.1,win.topColor) : win.lyricColor; win.bottomColor=bridge.settings.smartContrast ? win.contrastAt(.25,.85,win.bottomColor) : win.lyricColor } }
    Timer { id: hideUI; interval: 5000; running: true; onTriggered: { if(!settingsDrawer.opened) win.uiAwake = false; else restart() } }
    Shortcut { sequence: "F11"; onActivated: win.toggleFullscreen() }
    Shortcut { sequence: "F"; enabled: !settingsDrawer.opened; onActivated: win.toggleMode() }
    Shortcut { sequence: "Q"; enabled: !settingsDrawer.opened; onActivated: win.toggleQR() }
    Shortcut { sequence: "A"; enabled: !settingsDrawer.opened; onActivated: win.openSettings() }
    Shortcut { sequence: ","; enabled: !settingsDrawer.opened; onActivated: win.openSettings() }
    Shortcut { sequence: "Escape"; onActivated: { settingsDrawer.close(); if (win.visibility === Window.FullScreen) win.showNormal() } }
    HoverHandler { onPointChanged: win.wake() }

    Item {
        id: television
        anchors.centerIn: parent
        width: bridge.settings.tv ? Math.min(parent.width, parent.height * 1.51882) : parent.width
        height: bridge.settings.tv ? width / 1.51882 : parent.height
        Item {
            id: scene
            x: bridge.settings.tv ? parent.width * .08506 : 0
            y: bridge.settings.tv ? parent.height * .09563 : 0
            width: bridge.settings.tv ? parent.width * .82921 : parent.width
            height: bridge.settings.tv ? parent.height * .80773 : parent.height
            clip: true
            layer.enabled: true
            layer.textureSize: Qt.size(Math.max(2, Math.round(width * Math.min(1, 1920/width) * bridge.settings.quality * bridge.view.qualityScale)), Math.max(2, Math.round(height * Math.min(1,1920/width) * bridge.settings.quality * bridge.view.qualityScale)))
            layer.effect: ShaderEffect {
                property real curvature: win.egg || !bridge.settings.fish ? 0 : bridge.settings.lens / 500
                property real scan: win.egg || !bridge.settings.scanOn ? 0 : bridge.settings.scan / 100
                property real mask: win.egg ? 0 : bridge.settings.mask / 100
                property real vignette: win.egg ? 0 : bridge.settings.vignette / 100
                property real grain: win.egg ? 0 : bridge.settings.grain / 100
                property real flicker: !win.egg && win.motion && bridge.settings.flicker ? 1 : 0
                property real refresh: !win.egg && win.motion && bridge.settings.refresh ? 1 : 0
                property real tilt: !win.egg && win.motion && bridge.settings.tilt ? 1 : 0
                property real seconds: bridge.settings.reducedMotion ? 0 : win.seconds
                property vector2d resolution: Qt.vector2d(scene.width * Screen.devicePixelRatio, scene.height * Screen.devicePixelRatio)
                fragmentShader: "shaders/crt.qsb"
            }
            ShaderEffect {
                anchors.fill: parent
                property real seconds: bridge.settings.reducedMotion ? 0 : win.seconds
                property real pulseStart: win.pulseStart
                property real pulseDuration: win.pulseDuration
                property real strength: !win.motion || !(bridge.view.chill ? bridge.settings.pulseColor : bridge.settings.pulseColor || bridge.settings.pulseWhite) ? 0 : bridge.settings.strength / 100
                property real chill: bridge.view.chill ? 1 : 0
                property real style: bridge.settings.fluidStyle
                property color pulseColor: win.pulseColor
                property color colorA: bridge.view.palette[0]
                property color colorB: bridge.view.palette[1]
                property color colorC: bridge.view.palette[2]
                property color colorD: bridge.view.palette[3]
                property color colorE: bridge.view.palette[4]
                property real trails: win.motion && bridge.settings.trails && bridge.view.qualityScale>.65 ? 1 : 0
                Behavior on colorA { ColorAnimation { duration: 1200 } }
                Behavior on colorB { ColorAnimation { duration: 1200 } }
                Behavior on colorC { ColorAnimation { duration: 1200 } }
                Behavior on colorD { ColorAnimation { duration: 1200 } }
                Behavior on colorE { ColorAnimation { duration: 1200 } }
                fragmentShader: "shaders/background.qsb"
            }
            Rectangle { anchors.fill: parent; visible: win.egg !== ""; color: win.eggWhite ? "white" : "black" }
            Row {
                x: parent.width * .055; y: parent.height * .055; spacing: 20
                width: parent.width * .85
                opacity: win.uiAwake ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 500 } }
                Image { width: Math.min(82, scene.height * .12); height: width; source: bridge.view.cover; asynchronous: true; fillMode: Image.PreserveAspectCrop }
                Column {
                    width: parent.width - 105; anchors.verticalCenter: parent.verticalCenter; spacing: 5
                    Text { width: parent.width; text: bridge.view.title; color: win.topColor; font.pixelSize: scene.height<400 ? 16 : 21; font.bold: true; elide: Text.ElideRight }
                    Text { width: parent.width; text: bridge.view.artist; color: win.topColor; opacity: .8; font.pixelSize: scene.height<400 ? 13 : 17; elide: Text.ElideRight }
                }
            }
            Item {
                id: lettering
                anchors.centerIn: parent; width: parent.width*.88; height: lyricColumn.height+40
                scale: bridge.settings.beatBounce && win.motion ? 1+.02*Math.max(0,1-win.pulseAge/.2) : 1
                layer.enabled: bridge.settings.stroke>0 || bridge.settings.shadow>0
                layer.effect: ShaderEffect {
                    property vector2d pixelSize: Qt.vector2d(1/lettering.width,1/lettering.height)
                    property real stroke: bridge.settings.stroke
                    property real shadow: bridge.settings.shadow/100
                    property color edgeColor: win.lyricColor.r < .2 ? "white" : "black"
                    fragmentShader: "shaders/lettering.qsb"
                }
            Column {
                id: lyricColumn
                anchors.centerIn: parent; width: parent.width-40; spacing: 16
                Flow {
                    id: karaoke
                    width: parent.width; spacing: win.lyricSize * .25 * bridge.settings.wordSpacing
                    onPositioningComplete: {
                        var rows = []
                        for (var i = 0; i < wordRepeater.count; ++i) {
                            var word = wordRepeater.itemAt(i)
                            if (!word) continue
                            var last = rows.length ? rows[rows.length-1] : null
                            if (!last || Math.abs(last.y-word.y) > 1) {
                                last = {y: word.y, words: [], total: 0}; rows.push(last)
                            }
                            last.words.push(word); last.total += word.width
                        }
                        for (var r = 0; r < rows.length; ++r) {
                            var row = rows[r]
                            var x = (width-row.total-spacing*(row.words.length-1))/2
                            for (var j = 0; j < row.words.length; ++j) {
                                row.words[j].x = x; x += row.words[j].width + spacing
                            }
                        }
                    }
                    visible: !win.translationDisplay && bridge.lyric.groups.length > 0 && !bridge.lyric.title && !win.egg
                    height: visible ? implicitHeight : 0
                    Repeater {
                        id: wordRepeater
                        model: bridge.lyric.groups
                        Row {
                            required property var modelData
                            Repeater {
                                model: modelData.syllables
                                Item {
                                    required property var modelData
                                    width: baseText.implicitWidth; height: baseText.implicitHeight
                                    Text { id: baseText; text: win.displayText(modelData.text); font.family: win.lyricFont; font.pixelSize: win.lyricSize; color: win.lyricColor; opacity: .5 }
                                    Item {
                                        width: parent.width * Math.max(0, Math.min(1, (win.songPosition-modelData.t)/(modelData.end-modelData.t)))
                                        height: parent.height; clip: true
                                        Text { text: win.displayText(modelData.text); font: baseText.font; color: win.lyricColor }
                                    }
                                }
                            }
                        }
                    }
                }
                Text {
                    width: parent.width; visible: !karaoke.visible
                    text: win.egg === "eoo" && win.motion ? "E"+"O".repeat(1+Math.floor(Math.max(0,win.songPosition-bridge.lyric.start)/.085)%8) : win.displayText(win.translationDisplay && !bridge.lyric.title ? bridge.lyric.translated : bridge.lyric.text)
                    color: win.lyricColor; font.family: win.lyricFont
                    font.pixelSize: win.lyricSize; minimumPixelSize: 24; fontSizeMode: Text.Fit
                    wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
                    font.wordSpacing: win.lyricSize*.25*(bridge.settings.wordSpacing-1)
                    height: visible ? Math.min(implicitHeight, scene.height * .46) : 0
                }
                Text {
                    width: parent.width; text: win.translationDisplay ? bridge.lyric.translationStatus : bridge.lyric.back
                    visible: text.length > 0; height: visible ? implicitHeight : 0
                    color: win.lyricColor; opacity: .8; font.pixelSize: win.lyricSize * .4
                    wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
                }
            }
            }
            Column {
                x: parent.width * .055; y: parent.height - height - parent.height * .06
                width: parent.width * .55; spacing: 8; opacity: win.uiAwake ? 1 : 0
                Text { width: parent.width; text: bridge.view.queue ? "SIGUIENTE  ·  " + bridge.view.queue : ""; color: win.bottomColor; font.pixelSize: scene.height<400 ? 12 : 16; elide: Text.ElideRight }
                Text { width: parent.width; text: bridge.view.status + (bridge.view.lyricSource ? " · " + bridge.view.lyricSource : ""); color: win.bottomColor; opacity: .8; font.pixelSize: 12; elide: Text.ElideRight }
            }
            Text {
                anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: parent.width * .055
                width: parent.width*.31; elide: Text.ElideRight; horizontalAlignment: Text.AlignRight
                text: (bridge.view.playing ? "● " : "Ⅱ ") + bridge.view.genre + (bridge.view.bpm > 0 ? " · " + Math.round(bridge.view.bpm) + " BPM" : "")
                color: win.bottomColor; font.pixelSize: 13; opacity: win.uiAwake ? 1 : 0
            }
            StageEffects { id: stageFx; anchors.fill: parent; seconds: win.seconds; pulseAge: win.pulseAge; pulseColor: win.pulseColor; chill: bridge.view.chill; visible: !win.egg }
            Rectangle {
                x: parent.width * .07; y: parent.height * .965
                width: parent.width * .86; height: 2; radius: 1
                color: "#22ffffff"; opacity: win.uiAwake ? .65 : 0
                Rectangle {
                    width: parent.width * Math.max(0, Math.min(1, win.songPosition / Math.max(1,bridge.view.duration)))
                    height: parent.height; radius: 1; color: "#b9c7dc"
                }
            }
        }
        Image { anchors.fill: parent; source: "artwork/tv-frame-perreutt-v1.png"; visible: bridge.settings.tv; asynchronous: true }
    }
    TrackTransition { id: trackCurtain; objectName: "trackCurtain"; anchors.fill: parent; z: 50 }
    Row {
        anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 16; spacing: 8
        opacity: win.uiAwake || settingsDrawer.opened ? 1 : 0
        GlassButton { text: bridge.view.chill ? "Fluido · F" : "Fiesta · F"; onClicked: win.toggleMode() }
        GlassButton { text: "QR"; onClicked: win.toggleQR() }
        GlassButton { text: "⛶"; Accessible.name: "Pantalla completa"; onClicked: win.toggleFullscreen() }
        GlassButton { text: "Ajustes"; onClicked: win.openSettings() }
    }
    Rectangle {
        visible: bridge.settings.qrEnabled
        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 24
        width: Math.min(220,win.width*.3); height: width+42; radius: 16; color: "#f8ffffff"
        Image { x: 8; y: 8; width: parent.width-16; height: width; source: bridge.view.qrImage; smooth: false; fillMode: Image.PreserveAspectFit }
        Text { anchors.bottom: parent.bottom; anchors.bottomMargin: 14; anchors.horizontalCenter: parent.horizontalCenter; text: "Abrir canción en Spotify"; color: "#141820"; font.pixelSize: 12 }
        TapHandler { onTapped: win.toggleQR() }
    }
    SettingsPanel {
        id: settingsDrawer
        visualSource: television
        translationDisplay: win.translationDisplay
    }
}
