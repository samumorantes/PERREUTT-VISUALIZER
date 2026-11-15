import QtQuick
import QtQuick.Controls

Popup {
    id: panel
    objectName: "settingsPanel"
    popupType: Popup.Item
    required property Item visualSource
    property bool translationDisplay: false
    property int currentTab: 0
    width: Math.min(430, parent.width - 24)
    height: Math.min(740, parent.height - 88)
    x: parent.width - width - 16; y: 68
    padding: 22; modal: false; focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 180 } }
    exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: 120 } }
    background: Item {
        id: glass
        // Capture only the television, never this popup: no feedback loop.
        ShaderEffectSource {
            id: backdrop; sourceItem: panel.visualSource
            textureSize: Qt.size(Math.max(1,panel.visualSource.width/3),Math.max(1,panel.visualSource.height/3))
            live: panel.visible; visible: false; hideSource: false
        }
        Rectangle { x: -4; y: 6; width: parent.width+8; height: parent.height+8; radius: 26; color: "#38000000" }
        ShaderEffect {
            anchors.fill: parent
            property variant source: backdrop
            property vector4d region: {
                // Include geometry dependencies so resizing recomputes the map.
                var update = panel.x + panel.y + panel.visualSource.x + panel.visualSource.y
                var origin = glass.mapToItem(panel.visualSource, 0, 0)
                return Qt.vector4d(origin.x / panel.visualSource.width,origin.y / panel.visualSource.height,
                                   width / panel.visualSource.width,height / panel.visualSource.height)
            }
            property vector2d panelSize: Qt.vector2d(width,height)
            property vector2d backdropSize: Qt.vector2d(panel.visualSource.width,panel.visualSource.height)
            fragmentShader: "shaders/glass.qsb"
        }
    }
    contentItem: Column {
        spacing: 14
        Row {
            width: parent.width
            Column {
                width: parent.width - 44; spacing: 4
                Label { text: "Ajustes"; color: "white"; font.pixelSize: 23; font.weight: Font.DemiBold }
                Label { text: "Dale tu estilo a la fiesta"; color: "#b9c6dc"; font.pixelSize: 12 }
            }
            GlassButton { text: "✕"; Accessible.name: "Cerrar ajustes"; onClicked: panel.close() }
        }
        Row {
            id: tabs; width: parent.width; spacing: 5
            Repeater {
                model: ["Letra", "Ritmo", "CRT", "Guardar"]
                GlassButton {
                    required property string modelData
                    required property int index
                    width: (tabs.width - 15)/4; text: modelData
                    onClicked: panel.currentTab = index
                    background: Rectangle {
                        radius: 10; color: panel.currentTab === index ? "#387cdcc0" : "#16ffffff"
                        border.width: 1; border.color: panel.currentTab === index ? "#809ce9d1" : "#20ffffff"
                    }
                }
            }
        }
        Rectangle { width: parent.width; height: 1; color: "#22e4eaff" }
        ScrollView {
            id: scroller
            width: parent.width; height: panel.availableHeight - y - footer.height - 12
            clip: true; contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            Loader {
                width: scroller.availableWidth - 8
                sourceComponent: [lyricsPage, rhythmPage, crtPage, accountPage][panel.currentTab]
            }
        }
        Label { id: footer; text: "Los cambios se guardan automáticamente"; color: "#93a7bd"; font.pixelSize: 11 }
    }
    component Heading: Label {
        width: parent.width; color: "#a0ebd3"; font.pixelSize: 11; font.bold: true
        font.letterSpacing: 1.2; topPadding: 10
    }
    component Hint: Label { width: parent.width; wrapMode: Text.Wrap; color: "#bac5d8"; font.pixelSize: 12 }
    component Toggle: Switch {
        id: toggle; width: parent.width; font.pixelSize: 13; hoverEnabled: true
        indicator: Rectangle {
            x: toggle.width - width; y: (toggle.height-height)/2; width: 38; height: 22; radius: 11
            color: toggle.checked ? "#64d7b2" : "#40526378"; border.color: "#44e7f2ff"
            Rectangle { x: toggle.checked ? 18 : 3; y: 3; width: 16; height: 16; radius: 8; color: "white" }
        }
        contentItem: Text { text: toggle.text; color: "#e5ebf5"; font: toggle.font; verticalAlignment: Text.AlignVCenter; rightPadding: 48 }
    }
    Component {
        id: lyricsPage
        Column {
            spacing: 15
            SettingChoice { label: "Tema completo"; settingKey: "theme"; labels: ["Clásico", "Vaporwave", "Matrix", "Super Nintendo"]; values: ["classic","vaporwave","matrix","snes"] }
            Heading { text: "LETRA PRINCIPAL" }
            SettingSlider { label: "Tamaño"; settingKey: "fontSize"; minimum: 3; maximum: 16; increment: .5 }
            SettingChoice { label: "Tipografía"; settingKey: "font"; labels: ["Arcade", "Space Grotesk", "Impact", "Courier", "Georgia", "Sistema"]; values: ["arcade","grotesk","impact","courier","georgia","system"] }
            SettingSlider { label: "Palabras por frase"; settingKey: "phrase"; minimum: 1; maximum: 4; increment: 1 }
            SettingSlider { label: "Espacio entre palabras"; settingKey: "wordSpacing"; minimum: 0; maximum: 3; increment: .1 }
            Toggle { text: "MAYÚSCULAS"; checked: bridge.settings.upper; onToggled: bridge.setSetting("upper",checked) }
            Heading { text: "LEGIBILIDAD" }
            SettingSlider { label: "Grosor del borde"; settingKey: "stroke"; minimum: 0; maximum: 6; increment: 1 }
            SettingSlider { label: "Sombra"; settingKey: "shadow" }
            Toggle { text: "Contraste por zonas"; checked: bridge.settings.smartContrast; onToggled: bridge.setSetting("smartContrast",checked) }
            Toggle { text: "Easter eggs"; checked: bridge.settings.easterEggs; onToggled: bridge.setSetting("easterEggs",checked) }
            Heading { text: "SEGUNDA PANTALLA" }
            Hint { text: "La letra original aquí, la traducción en otra ventana." }
            SettingChoice { label: "Idioma original"; settingKey: "fromLang"; labels: ["Español","English","Français","Português","Italiano","Deutsch"]; values: ["es","en","fr","pt","it","de"] }
            SettingChoice { label: "Traducción"; settingKey: "toLang"; labels: ["Español","English","Français","Português","Italiano","Deutsch"]; values: ["es","en","fr","pt","it","de"] }
            GlassButton { width: parent.width; text: "Abrir segunda pantalla"; visible: !panel.translationDisplay; onClicked: bridge.openTranslation() }
            Hint { text: "Traducción por frase con MyMemory. Requiere conexión y está sujeta a cuota." }
        }
    }
    Component {
        id: rhythmPage
        Column {
            spacing: 15
            Heading { text: "FLASHES" }
            SettingChoice { label: "Paleta"; settingKey: "palette"; labels: ["RGB intenso","Pastel","Neón","Atardecer","Océano","Blanco y negro"]; values: ["rgb","pastel","neon","sunset","ocean","byn"] }
            SettingChoice { label: "Modo visual"; settingKey: "mood"; labels: ["Automático", "Fiesta", "Fluido"]; values: ["auto","party","chill"] }
            SettingSlider { label: "Fuerza del flash"; settingKey: "strength" }
            Toggle { text: "Pulso de color"; checked: bridge.settings.pulseColor; onToggled: bridge.setSetting("pulseColor",checked) }
            Toggle { text: "Flash blanco"; checked: bridge.settings.pulseWhite; onToggled: bridge.setSetting("pulseWhite",checked) }
            SettingSlider { label: "Umbral base · más bajo = más sensible"; settingKey: "threshold"; minimum: 1.5; maximum: 10; increment: .25 }
            Toggle { text: "Adaptar al ruido de la canción"; checked: bridge.settings.autoThreshold; onToggled: bridge.setSetting("autoThreshold",checked) }
            Hint { text: bridge.view.thresholdStatus }
            Heading { text: "ECUALIZADOR DE DETECCIÓN" }
            SettingSlider { label: "Graves · 35–220 Hz (%)"; settingKey: "bassGain"; maximum: 200; increment: 5 }
            SettingSlider { label: "Agudos · 2,5–10 kHz (%)"; settingKey: "trebleGain"; maximum: 200; increment: 5 }
            Hint { text: "Medios excluidos. 100% = normal; 0% desactiva la banda. Solo afecta a la detección de percusión de Windows, no al sonido ni al mapa de beats." }
            Heading { text: "SINCRONIZACIÓN" }
            SettingChoice { label: "Fuente del ritmo"; settingKey: "source"; labels: ["Percusión de Windows", "Mapa / calibración"]; values: ["loopback","grid"] }
            Hint { text: bridge.view.audio }
            SettingChoice { label: "Disparar con"; settingKey: "timing"; labels: bridge.settings.source === "loopback" ? ["Golpes", "Acentos fuertes", "Posibles drops"] : ["Beats", "Compases", "Secciones"]; values: ["beats","bars","sections"] }
            SettingChoice { label: "Perfil de esta canción"; settingKey: "genre"; current: bridge.view.genreKey; labels: ["Automático", "Salsa", "Bachata", "Reguetón", "Merengue", "Cumbia", "Electrónica", "Pop", "Rock", "Mixto"]; values: ["auto","salsa","bachata","reggaeton","merengue","cumbia","electronic","pop","rock","mixed"] }
            Hint { text: bridge.view.genreOrigin }
            Heading { text: "AJUSTE FINO" }
            SettingSlider { label: "Desfase (ms)"; settingKey: "offset"; minimum: -500; maximum: 500; increment: 10; current: bridge.view.offset }
            Hint { text: "Negativo retrasa el flash. El audio en directo no puede anticipar un golpe." }
            Row { spacing: 8; GlassButton { text: "Marcar beat"; onClicked: bridge.tapBeat() } GlassButton { text: "Restablecer"; onClicked: bridge.resetRhythm() } }
            Hint { text: bridge.view.message; visible: text.length > 0 }
            Heading { text: "FONDO Y EFECTOS" }
            Toggle { text: "Detectar baladas automáticamente"; checked: bridge.settings.autoMood; onToggled: bridge.setSetting("autoMood",checked) }
            SettingChoice { label: "Fondo fluido"; settingKey: "fluidStyle"; labels: ["Ondas", "Espiral", "Plasma", "Aurora"]; values: [0,1,2,3] }
            Toggle { text: "Estelas"; checked: bridge.settings.trails; onToggled: bridge.setSetting("trails",checked) }
            Toggle { text: "Espectro de ritmo"; checked: bridge.settings.spectrum; onToggled: bridge.setSetting("spectrum",checked) }
            Toggle { text: "Rebote de la letra"; checked: bridge.settings.beatBounce; onToggled: bridge.setSetting("beatBounce",checked) }
            Toggle { text: "Partículas en drops"; checked: bridge.settings.dropFx; onToggled: bridge.setSetting("dropFx",checked) }
            GlassButton { text: "Probar partículas"; onClicked: bridge.testDrop() }
            Toggle { text: "QR de la canción · Q"; checked: bridge.settings.qrEnabled; onToggled: bridge.setSetting("qrEnabled",checked) }
            Hint { text: "El QR abre la canción en Spotify. Las barras representan el ritmo detectado." }
            Heading { text: "TRANSICIÓN DE CANCIÓN" }
            SettingChoice { label: "Efecto"; settingKey: "transition"; labels: ["TV antigua", "Obturador", "Vinilo", "Flash de color", "Ninguna"]; values: ["tv","shutter","vinyl","flashcolor","none"] }
            GlassButton { width: parent.width; text: "Probar transición"; onClicked: bridge.testTransition() }
        }
    }
    Component {
        id: crtPage
        Column {
            spacing: 15
            Heading { text: "CRISTAL" }
            GlassButton { text: "CRT · todo / nada"; onClicked: bridge.toggleCrt() }
            Toggle { text: "Mueble de TV"; checked: bridge.settings.tv; onToggled: bridge.setSetting("tv", checked) }
            Toggle { text: "Ojo de pez"; checked: bridge.settings.fish; onToggled: bridge.setSetting("fish",checked) }
            Toggle { text: "Scanlines"; checked: bridge.settings.scanOn; onToggled: bridge.setSetting("scanOn",checked) }
            Toggle { text: "Parpadeo CRT"; checked: bridge.settings.flicker; onToggled: bridge.setSetting("flicker",checked) }
            Toggle { text: "Inclinación"; checked: bridge.settings.tilt; onToggled: bridge.setSetting("tilt",checked) }
            Toggle { text: "Banda de refresco"; checked: bridge.settings.refresh; onToggled: bridge.setSetting("refresh",checked) }
            SettingSlider { label: "Curvatura"; settingKey: "lens" }
            SettingSlider { label: "Líneas CRT"; settingKey: "scan" }
            SettingSlider { label: "Máscara RGB"; settingKey: "mask" }
            SettingSlider { label: "Viñeta"; settingKey: "vignette" }
            SettingSlider { label: "Grano"; settingKey: "grain" }
            Heading { text: "RENDIMIENTO" }
            Toggle { text: "Calidad automática"; checked: bridge.settings.autoQuality; onToggled: bridge.setSetting("autoQuality",checked) }
            Hint { text: bridge.view.performance }
            SettingSlider { label: "Resolución de efectos"; settingKey: "quality"; minimum: .5; maximum: 1; increment: .1 }
            Toggle { text: "Movimiento reducido"; checked: bridge.settings.reducedMotion; onToggled: bridge.setSetting("reducedMotion", checked) }
        }
    }
    Component {
        id: accountPage
        Column {
            spacing: 15
            Heading { text: "ESTILOS POR GÉNERO" }
            Hint { text: "Elige un aspecto. La sensibilidad y la sincronización se conservan. Puedes guardarlo para una canción, artista o álbum más abajo." }
            Repeater {
                model: bridge.genreStyles
                Rectangle {
                    required property var modelData
                    width: parent.width; height: recipeContent.height+24; radius: 14
                    color: modelData.active ? "#224bd9ae" : "#12ffffff"
                    border.color: modelData.active ? "#809ce9d1" : "#28ffffff"
                    Column {
                        id: recipeContent; x: 12; y: 12; width: parent.width-24; spacing: 8
                        Label { width: parent.width; text: modelData.name; color: "white"; font.pixelSize: 16; font.bold: true }
                        Hint { text: modelData.description }
                        Row {
                            spacing: 6
                            Repeater { model: modelData.colors; Rectangle { required property string modelData; width: 22; height: 8; radius: 4; color: modelData } }
                        }
                        GlassButton { text: modelData.active ? "Aplicado" : "Aplicar estilo"; enabled: !modelData.active; onClicked: bridge.applyGenreStyle(modelData.key) }
                    }
                }
            }
            Heading { text: "PRESETS POR MÚSICA" }
            Toggle { text: "Bloquear configuración global"; checked: bridge.settings.globalLock; onToggled: bridge.setSetting("globalLock",checked) }
            Hint { text: bridge.view.preset ? "Activo: " + bridge.view.preset : "Guarda este aspecto para una canción, artista o álbum." }
            Row {
                spacing: 6
                GlassButton { text: "Canción"; onClicked: bridge.savePreset("song") }
                GlassButton { text: "Artista"; onClicked: bridge.savePreset("artist") }
                GlassButton { text: "Álbum"; onClicked: bridge.savePreset("album") }
            }
            Repeater {
                model: bridge.presets
                Row {
                    required property var modelData
                    width: parent.width; spacing: 6
                    Label { width: parent.width-46; anchors.verticalCenter: parent.verticalCenter; text: (modelData.active ? "● " : "")+modelData.label; elide: Text.ElideMiddle; color: "#dce5f3"; font.pixelSize: 12 }
                    GlassButton { text: "×"; Accessible.name: "Borrar " + modelData.label; onClicked: bridge.deletePreset(modelData.key) }
                }
            }
            GlassButton { text: "Ver / importar presets"; onClicked: presetEditor.visible=!presetEditor.visible }
            Column {
                id: presetEditor; width: parent.width; spacing: 8; visible: false
                TextArea { id: presetJson; width: parent.width; height: 130; text: bridge.presetSummary; wrapMode: TextEdit.WrapAnywhere; selectByMouse: true; color: "white"; font.pixelSize: 11; background: Rectangle { radius: 8; color: "#50000000" } }
                Row { spacing: 8; GlassButton { text: "Copiar"; onClicked: bridge.copyPresets() } GlassButton { text: "Importar JSON"; onClicked: bridge.importPresets(presetJson.text) } }
            }
            GlassButton { text: "Borrar todos los presets"; onClicked: panel.confirmAction("presets", "¿Borrar todos los presets guardados?") }
            Heading { text: "PALETA DEL FLUIDO" }
            Toggle { text: "Paleta manual · ignora portada"; checked: bridge.settings.customPal; onToggled: bridge.setSetting("customPal",checked) }
            Repeater {
                model: 5
                Row {
                    required property int index
                    width: parent.width; spacing: 10
                    Rectangle { width: 36; height: 36; radius: 9; color: bridge.settings.customPalCols[index]; border.color: "#60ffffff" }
                    TextField { width: parent.width-46; height: 36; text: bridge.settings.customPalCols[index]; maximumLength: 7; selectByMouse: true; color: "white"; onEditingFinished: bridge.setPaletteColor(index,text); background: Rectangle { radius: 8; color: "#30000000"; border.color: "#40ffffff" } }
                }
            }
            GlassButton { text: "Colores aleatorios"; onClicked: bridge.randomPalette() }
            Heading { text: "SPOTIFY" }
            Hint { text: bridge.view.status }
            TextField {
                id: clientId; width: parent.width; height: 42; placeholderText: "Client ID de Spotify"; selectByMouse: true
                color: "white"; placeholderTextColor: "#aebdd2"; leftPadding: 12
                background: Rectangle { radius: 10; color: "#30000000"; border.color: "#40ffffff" }
            }
            GlassButton { width: parent.width; text: "Conectar Spotify"; onClicked: bridge.connectSpotify(clientId.text) }
            GlassButton { width: parent.width; text: "Desconectar Spotify"; onClicked: bridge.disconnectSpotify() }
            Hint { text: bridge.view.message; visible: text.length > 0 }
            Hint { text: "Solo la autorización se abre en el navegador. Reproduce Spotify en este PC para detectar su percusión." }
            GlassButton { width: parent.width; text: "Restablecer configuración"; onClicked: panel.confirmAction("reset", "¿Restablecer los ajustes? Se conservarán tus presets.") }
        }
    }
    function confirmAction(action, message) { confirmation.action=action; confirmation.message=message; confirmation.open() }
    Popup {
        id: confirmation
        property string action
        property string message
        parent: panel.contentItem; anchors.centerIn: parent; width: parent.width; padding: 18; modal: true
        background: Rectangle { radius: 16; color: "#f0212c3b"; border.color: "#6089e6c8" }
        contentItem: Column {
            spacing: 16
            Label { width: parent.width; text: confirmation.message; wrapMode: Text.Wrap; color: "white" }
            Row { spacing: 10; GlassButton { text: "Cancelar"; onClicked: confirmation.close() } GlassButton { text: "Confirmar"; onClicked: { if (confirmation.action === "presets") bridge.clearPresets(); else bridge.resetSettings(); confirmation.close() } } }
        }
    }
}
