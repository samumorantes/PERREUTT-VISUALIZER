# FIESTA Native · plataformas

Las ediciones comparten interfaz Qt Quick, presets, shaders, letras, traducción
y detector. Cambian el render, la captura y el empaquetado.

## Descargas y comprobaciones

**Native builds** compila Windows x64, Linux x64, macOS Apple Silicon y macOS
Intel en sus propios runners. Cada artefacto incluye paquete, SHA-256 y una
captura/informe del arranque de dos ventanas, sin Spotify ni captura de audio.
Los artefactos de Actions requieren sesión GitHub y caducan; los tags publican
los paquetes en Releases.

Un build correcto comprueba compilación, lógica y render de prueba. **No verifica
la captura física, los permisos, Spotify ni los distintos monitores del usuario.**
Esos aspectos necesitan comprobación en el equipo destino. Las máquinas
virtuales tampoco representan el rendimiento de una GPU real.

## Windows

Windows 10/11 x64. Instala el EXE por usuario, sin administrador.
Direct3D 11 dibuja las escenas; WASAPI analiza la salida predeterminada.
El instalador no está firmado. Conserva datos al actualizar o desinstalar.
Consulta [la guía de uso](../DESKTOP.md).

## macOS

macOS 13 o posterior. Descarga **arm64** para Apple Silicon o **x86_64** para
Intel. Abre el DMG y arrastra **FIESTA.app** a **Aplicaciones**. Usa Metal.
Los builds tienen firma ad hoc de empaquetado, pero no firma Developer ID ni
notarización: macOS puede bloquearlos. Solo si confías en su procedencia, usa
**Abrir igualmente** en Privacidad y seguridad. No desactives Gatekeeper.

### Audio sin micrófono

1. Instala [BlackHole 2ch](https://existential.audio/blackhole/) desde su proveedor.
   Es un controlador externo; FIESTA no lo instala ni lo incluye.
2. En **Configuración de Audio MIDI**, crea un **dispositivo de salida múltiple**
   con altavoces/auriculares y **BlackHole 2ch**.
3. Usa el dispositivo físico como reloj principal y activa la corrección de
   deriva en BlackHole. Configura ambos a 48 kHz.
4. Selecciona esa salida múltiple como salida del sistema y reproduce Spotify.
5. Abre FIESTA y permite el acceso de audio cuando macOS lo solicite. El permiso
   aparece como «Micrófono» porque BlackHole expone una entrada CoreAudio;
   FIESTA selecciona exclusivamente **BlackHole 2ch**, no el micrófono físico.

Sin BlackHole, muestra el motivo y permite usar **Mapa / calibración**;
no cambia al micrófono. Elegir solo BlackHole como salida envía audio al
visualizador pero no a los altavoces. La mezcla virtual introduce latencia;
ajusta el desfase de percusión si hace falta.

## Linux

Paquete x86_64 construido en Ubuntu 22.04 (glibc 2.35). Requiere una sesión
gráfica con OpenGL y **PulseAudio** o **PipeWire con pipewire-pulse**.
No sirve directamente en Alpine/musl ni se garantiza compatibilidad con todas
las distribuciones. X11/XWayland es la referencia del build.

En Ubuntu/Debian, instala con el gestor del sistema las bibliotecas
`libegl1 libopengl0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4
libxcb-keysyms1 libxcb-image0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0
libxcb-randr0 libxcb-sync1 libxcb-xinerama0 libpulse0`.
Qt y Python van incluidos; el servidor de audio no.

Extrae el `.tar.gz` en una carpeta permanente y ejecuta `FIESTA/FIESTA`.
Opcionalmente ejecuta `sh FIESTA/install-linux.sh`: registra esa carpeta en el
menú sin administrador. No la muevas después. Para quitar el acceso, elimina
`~/.local/share/applications/fiesta-native.desktop` y
`~/.local/share/icons/hicolor/256x256/apps/fiesta-native.png`
(o las rutas equivalentes bajo `XDG_DATA_HOME`).

La captura elige el monitor de la salida predeterminada y revisa cambios de
dispositivo cada tres segundos. No selecciona entradas físicas. Si aparece
«No hay monitor de salida», comprueba el servidor Pulse y que Spotify use la
salida predeterminada. Un ruteo especial puede necesitar ajustes en tu mezclador.

## Datos personales

| Sistema | Carpeta |
| --- | --- |
| Windows | `%LOCALAPPDATA%/FIESTA-Native` |
| macOS | `~/Library/Application Support/FIESTA-Native` |
| Linux | `$XDG_DATA_HOME/FIESTA-Native`, o `~/.local/share/FIESTA-Native` |

Aquí se guardan ajustes, presets, sesión y logs. Nunca se incluyen en paquetes.
Las credenciales de una instalación fuente anterior se importan en el primer
arranque normal; las pruebas de humo no las importan.

## Desarrollo y empaquetado

Python 3.11 de la arquitectura destino; instala `requirements-desktop.txt`
en `.venv-desktop`. En Unix activa con `source .venv-desktop/bin/activate`.

```sh
python scripts/build_native.py --prepare-only
python fiesta_desktop.py
```

`--prepare-only` convierte fuentes y compila GLSL a QSB con variantes para
Direct3D, Metal y OpenGL. Para empaquetar:

```sh
python scripts/build_native.py
python scripts/check_native.py
python scripts/package_native.py
```

En Linux sin pantalla, el check necesita `xvfb-run -a` y Mesa. En macOS necesita
una sesión gráfica. En Windows usa `build_desktop.ps1` y
`build_installer.ps1 -SkipBuild -Version 2.6.0` (Inno Setup 6).

Los paquetes Unix van a `dist/packages`. PyInstaller no permite compilar macOS
desde Windows: cada paquete se genera en su propio OS. Qt se distribuye
dinámicamente con sus avisos y bibliotecas reemplazables.
