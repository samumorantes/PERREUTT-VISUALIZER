# 🎉 FIESTA — Visualizador de letras en tiempo real

Muestra la **frase que se está cantando** en pantalla grande, con fondos que laten al ritmo de la música. Conéctalo a tu Spotify y convierte cualquier pantalla en un karaoke de fiesta.

![FIESTA](fiesta.ico)

## Aplicación nativa para Windows

La edición nativa usa **Qt Quick y Direct3D 11**, sin navegador ni WebView.
Instala con [FIESTA Native Setup 2.5.0](releases/FIESTA-Native-Setup-2.5.0.exe)
(Windows 10/11 x64, por usuario, con desinstalador y accesos directos).
Abre [FIESTA.exe](dist/FIESTA/FIESTA.exe) y conserva toda su carpeta.
Incluye los controles del visualizador web: Spotify, karaoke, percusión WASAPI,
temas, paletas, presets por música, transiciones, partículas, CRT, QR, easter eggs
y segunda pantalla traducida. [Inventario de funciones](desktop/FEATURE_PARITY.md).
El lanzador ahora da prioridad a esta edición; `--web` abre la anterior.
Consulta [DESKTOP.md](DESKTOP.md) para construirla, conectarla y configurar sus
efectos nativos. Tras construirlo, `install.ps1`
instala la edición nativa por usuario; `install.ps1 -Web` conserva la instalación
antigua descrita más abajo.

## ✨ Qué hace

- **Letra sincronizada** palabra a palabra y **karaoke por sílaba** (Spicy Lyrics → Spotify → LRCLIB → lyrics.ovh, con respaldo: nunca dice "NO LYRICS")
- **Modo fiesta**: negro → golpe de color → caída exponencial → negro entre beats; intensidad configurable
- **Modo fluido** (auto en baladas): gradiente vivo con los colores de la portada del álbum
- **Estética CRT arcade**: scanlines, fósforos RGB, ojo de pez — todo configurable
- **Título 7s** al empezar cada canción ("♪ Canción ♪")
- **Transición** al cambiar de canción: TV antigua, obturador, vinilo con la portada, flash de color
- **Cola de reproducción** y estado de conexión en pantalla
- **Mueble de TV vintage** (activable), lente ojo de pez real, temas completos
- **Presets por canción/artista/álbum**, paleta manual, espectro CRT, partículas en drops
- **QR de la canción en Spotify**, segunda pantalla con la letra traducida y contraste inteligente por zonas
- **Calidad adaptativa** para mantener una cadencia estable, también en pantallas de 60 Hz (lente, estelas y resolución del fluido)
- **Easter eggs** 🐰

## 🚀 Instalación (Windows)

1. Instala [Python 3.11+](https://www.python.org/downloads/) (marca "Add to PATH")
2. Crea una app gratuita en [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) y pega tu **Client ID** en `config.json` (añade `http://127.0.0.1:8888/callback` como Redirect URI)
3. Doble clic en:

```
install.ps1 -Web   →   instalación de la edición web
```

Eso instala todo: accesos directos con icono, auto-arranque y abre FIESTA.

### 🎤 Letras de Spicy Lyrics (opcional, máxima precisión)

FIESTA usa la API de desarrolladores de **Spicy Lyrics** — el mismo catálogo
comunitario TTML que la extensión de Spicetify, con tiempos por sílaba y coros.
Es la fuente más precisa; sin clave la app sigue funcionando con Spotify/LRCLIB.

1. Entra en [developers.spicylyrics.org](https://developers.spicylyrics.org), crea
   una aplicación y copia tu clave `sl_sk_...` (solo se muestra una vez).
2. Guárdala en un archivo `spicy_key.txt` junto a `server.py` (una línea, sin
   comillas). También vale la variable de entorno `SPICYLYRICS_KEY`.
3. Reinicia FIESTA.

`spicy_key.txt` está en `.gitignore`: no se sube al repositorio.

## 🖱️ Uso diario

Doble clic en el acceso directo **FIESTA** (Escritorio o Menú Inicio). Dale play en Spotify. Nada más.

### Doble pantalla con traducción

En **Ajustes → Letra → Doble pantalla**, elige el idioma de la canción y el
idioma de destino, y pulsa **Abrir segunda pantalla**. Por defecto: español
→ inglés. También están disponibles francés, portugués, italiano y alemán.
Arrastra la nueva ventana al otro monitor y usa **Pantalla completa** en sus
ajustes (o F11). Volver a pulsar el botón reutiliza la ventana abierta.

La ventana original conserva la letra original; la segunda muestra la
traducción como texto principal, sin subtítulos traducidos. Ambas consultan
la misma reproducción de Spotify y la segunda sigue funcionando si cierras
la primera. La sincronización de la traducción es **por frase**, sin atribuir
los tiempos de las palabras originales a las traducidas.

Se preparan las próximas frases y se reutilizan traducciones repetidas.
La traducción automática usa MyMemory por Internet, con sus límites de cuota
y calidad; si una frase tarda o falla, se indica en pantalla. Si el navegador
bloquea la ventana, permite ventanas emergentes para la dirección de FIESTA.

## 🌍 Acceso desde el móvil (fuera de casa)

Doble clic en `host_public.cmd` y copia el enlace `https://…trycloudflare.com` que
aparece en la ventana. Ábrelo en el móvil: funciona desde cualquier red, sin abrir
puertos en el router.

- El PC tiene que estar encendido con FIESTA corriendo (el lanzador ya lo arranca).
- Deja la ventana de `host_public.cmd` abierta: si la cierras, el enlace deja de funcionar.
- El enlace cambia cada vez que abres `host_public.cmd` (túnel rápido de Cloudflare, sin cuenta).
- Cualquiera que tenga el enlace puede ver el visualizador, así que no lo compartas fuera de casa.

## ⚙️ Personalización

Clic en ⚙️ dentro de la app: tamaño/fuente/color de letra, paletas, fuerza de los flashes, efectos CRT, transiciones… y botón de reset.

### Ajustar los flashes al ritmo

**Nuevo: percusión del PC, sin micrófono.** En Ajustes → Ritmo → Sincronización,
la fuente predeterminada analiza la salida de audio de Windows y dispara flashes
con sus ataques reales. Usa la misma salida que Spotify; si Spotify Connect suena
en otro aparato, selecciona «Mapa de Spotify / calibración manual».

Instala el soporte opcional una vez con `powershell -ExecutionPolicy Bypass -File
setup_audio.ps1` (Python 3.11+). Crea un entorno local `.venv-audio`; el lanzador lo
elige automáticamente. Reinicia el servidor después de instalarlo. Para arrancar
directamente: `.venv-audio\Scripts\python.exe server.py`. Sin estas dependencias,
las letras y el modo de mapas siguen funcionando.

El selector de género propone categorías mediante etiquetas de los artistas de
Spotify; **no confirma el género de cada grabación**. Puedes corregirlo por canción.
Sin datos, muestra «Sin clasificar» y sigue detectando ataques generales. Salsa,
bachata y reguetón tienen perfiles distintos de sensibilidad a graves, medios y
agudos; ninguno impone un BPM o inventa golpes. El tempo mostrado es estimado y
puede ser mitad/doble. «Acentos fuertes» no identifica el inicio del compás;
«Posibles drops» es una estimación por energía, no una anotación musical confirmada.

La captura no graba archivos ni sube audio y se libera cuando no quedan ventanas
visibles reproduciendo. También recoge notificaciones y otros sonidos de esa
salida. En silencio o sin dispositivo no se generan flashes ficticios. Se puede
retrasar un golpe en vivo, pero anticiparlo requiere un mapa previo. Las dos
pantallas reciben la misma captura; la red y el refresco pueden introducir desfase.

Consulta el [estudio de ritmos, fuentes y límites](docs/ritmo-y-generos.md).

**Modo mapa / calibración:**

En **Ajustes → Ritmo → Sincronización** se indica si hay beats del análisis
de Spotify o una estimación. Si falta el análisis, pulsa **Marcar beat** entre
4 y 8 veces siguiendo golpes regulares: se guardan el tempo y la fase para esa
canción. Este ajuste supone un tempo constante; no detecta drops ni cambios de BPM.

El control de adelanto/retraso permite compensar la salida de audio o pantalla:
positivo adelanta los flashes, negativo los retrasa, sin mover las letras.
Los ajustes se guardan por canción y se comparten entre las ventanas del mismo
navegador. **Restaurar ritmo de la canción** elimina la calibración.
Sin análisis no se inventan drops. Las secciones de Spotify indican cambios
estructurales, que no siempre coinciden con un drop.

### Efectos de shaders.com

En **Ajustes → Ritmo → Fondo fluido** puedes elegir Fluido orgánico,
Remolino, Plasma o Aurora. Usan la paleta de la portada o tu paleta manual
y reaccionan al tempo y los beats. Las estelas, el CRT, el grano y las
transiciones TV/obturador/color también usan la biblioteca MIT de
[shaders.com](https://shaders.com/). La viñeta se dibuja en CSS con una elipse
centrada, para que su borde siga la curva del tubo en vez de un rectángulo.

Los efectos WebGPU se cargan desde el propio servidor, sin cuenta, CDN ni
telemetría. Si WebGPU no está disponible, falla la GPU o la calidad adaptativa
baja al mínimo, se usan los efectos clásicos. `?legacyEffects` permite forzar
esa alternativa. La lente SVG sigue curvando las letras y la interfaz junto
con los fondos: capturar HTML mediante WebGPU aún requiere funciones
experimentales del navegador. El vinilo, espectro y partículas conservan su
implementación actual.

El archivo público `assets/fiesta-shaders.js` ya está compilado: ejecutar
FIESTA sigue requiriendo solo Python. Para modificar los efectos:

```powershell
npm ci
npm run build:effects
```

Código: `src/fiesta-shaders.js`. Dependencias fijadas en `package-lock.json`;
licencias en [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## 🗑️ Desinstalar

Menú Inicio → "Uninstall FIESTA".

---
Hecho con ❤️ y muchos beats. v2.3 "SYNC"
