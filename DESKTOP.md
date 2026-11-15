# FIESTA Native para Windows

## Instalador EXE

Ejecuta [FIESTA-Native-Setup-2.5.0.exe](releases/FIESTA-Native-Setup-2.5.0.exe).
Instala para tu usuario en `%LOCALAPPDATA%/Programs/FIESTA-Native`, permite
elegir carpeta, crea accesos directos y registra la desinstalación en Windows.
No requiere permisos de administrador. Las actualizaciones usan la misma
identidad y carpeta; los ajustes y la sesión en `%LOCALAPPDATA%/FIESTA-Native`
se conservan incluso al desinstalar. No incluye credenciales del desarrollador.
El instalador no está firmado con un certificado de editor; Windows puede
mostrar una advertencia de editor desconocido. Se incluye un SHA-256 para
comprobar la integridad, que no sustituye la firma de un editor.

Para reconstruir: instala Inno Setup 6 desde https://jrsoftware.org y ejecuta
`powershell -ExecutionPolicy Bypass -File build_installer.ps1` después de preparar
el entorno con `setup_desktop.ps1`. Acepta `-Compiler RUTA\ISCC.exe` y
`-SkipBuild` para empaquetar un `dist/FIESTA` ya compilado. Los resultados van
a `releases/`. Cierra la app del checkout antes de reconstruir su ejecutable.

## Edición portable

Abre `FIESTA.exe` dentro de la carpeta `dist/FIESTA`. Conserva `_internal` junto
al ejecutable: no necesita Python instalado ni un navegador para dibujar.
Usa Qt Quick, Direct3D 11 y shaders propios. Spotify, letras, traducción y audio
trabajan fuera del hilo de la interfaz. No incluye Electron, Chromium ni WebView.

## Uso

- Reproduce Spotify en este PC. Ajustes → Sincronización → Percusión de la salida
  de Windows analiza el dispositivo de salida predeterminado, sin micrófono.
- **Ritmo → Ecualizador de detección:** solo graves (35–220 Hz) y agudos
  (2,5–10 kHz) pueden disparar los flashes de percusión. Los medios quedan fuera
  también del cálculo de tempo y del contexto de energía del detector nativo.
  Cada banda tiene sensibilidad de 0 a 200%: 100% normal, 0% desactivada.
  Los ajustes se conservan al aplicar presets visuales y reinician el aprendizaje
  del umbral. Este filtro analiza el audio; no modifica el sonido de Spotify
  ni se aplica al modo Mapa / calibración. Separa frecuencias, no instrumentos:
  una voz u otro sonido con armónicos graves/agudos todavía puede producir ataques.
- El umbral inicial es 1,75 y la fuerza del flash 85%; bajar el umbral admite
  más golpes. El detector deja pasar ataques suaves desde 1,25 antes del filtro
  por género, conservando el bloqueo por silencio. Los acentos fuertes
  requieren tres puntos más. Los drops son candidatos, no marcas infalibles.
- **Adaptar al ruido de la canción** viene activado en Ritmo. Aprende durante
  los primeros dos segundos y observa una ventana móvil de seis segundos de
  ataques normalizados. Si hay muchos ataques débiles entre otros más fuertes,
  sube suavemente el umbral; vuelve a bajarlo al despejarse el fondo. No sube
  simplemente porque el volumen sea alto ni por un patrón rápido uniforme.
  El control manual pasa a ser el umbral base, y debajo aparece el efectivo.
  Puedes desactivar la adaptación para volver al umbral fijo. Se reinicia al
  cambiar de canción, pausar, buscar o perder la captura; no modifica el mapa
  ni inventa beats. Es una heurística de transitorios, no separación de instrumentos.
- Género automático usa etiquetas del artista como sugerencia. Puedes corregirlo
  por canción. Salsa, bachata y reguetón no equivalen a contar 3, 4 y 4 golpes:
  la salsa suele escribirse en 4/4 y su clave puede abarcar dos compases.
- Mapa / calibración usa análisis Spotify si está disponible; de lo contrario
  indica que el ritmo es estimado. Marcar beat permite ajustar una cuadrícula
  constante. La captura en directo tiene latencia y no puede anticipar golpes.
- F11 alterna pantalla completa; Esc sale. Ajustes permite cambiar lente,
  tipografía, intensidad, resolución, fondos y movimiento reducido.
  El panel de cristal desenfoca la escena con un shader nativo y organiza los
  controles en Letra, Ritmo, CRT y Guardar. La captura del fondo solo se actualiza
  mientras el panel está abierto. La lente conserva los límites de la escena,
  evitando repetir o estirar píxeles del borde incluso a curvatura 100.
- Doble pantalla abre otra ventana **nativa**, colocada en otro monitor si existe.
  Comparte el mismo reloj. La traducción de MyMemory se sincroniza por frase;
  requiere Internet y está sujeta a cuota. Cerrar una ventana deja la otra abierta.
- Minimizar todas las ventanas detiene su animación y libera la captura de audio.
- Al cambiar de canción, la escena anterior se conserva hasta quedar cubierta.
  La portada se precarga y el contenido nuevo se dibuja detrás de la transición
  en ambas ventanas antes de abrirla. No aparece «Cargando canción…». Los modos
  sin transición o con movimiento reducido hacen el cambio cubierto sin animar.
  Una portada que tarda más de 2,5 s se omite; un error de Spotify libera la
  transición y se explica en Ajustes, sin sustituir la letra por mensajes de carga.

## Spotify y datos

Los ajustes y credenciales se guardan en `%LOCALAPPDATA%/FIESTA-Native`.
Al ejecutar desde el checkout o su `dist/FIESTA`, se copian las credenciales
existentes una sola vez, si faltan. **No se incluyen en el ejecutable**.
En otro PC, introduce el Client ID en Ajustes → Conectar Spotify. Registra
`http://127.0.0.1:8888/callback` en Spotify. Solo la autorización abre el navegador;
después vuelve a la aplicación. Si el servidor web anterior ocupa 8888, ciérralo
antes de reconectar. No hace falta cerrarlo para usar una sesión ya importada.
La clave opcional de Spicy Lyrics va en `spicy_key.txt` dentro de esa carpeta.
Errores de arranque: `startup-error.log`; avisos de Qt: `desktop.log`.

## Alcance de esta edición

Los controles y funciones del visualizador web tienen equivalente nativo.
Consulta el inventario en [desktop/FEATURE_PARITY.md](desktop/FEATURE_PARITY.md).
Incluye los cuatro temas, seis fuentes, seis paletas de fiesta, paleta de portada
o cinco colores manuales, cuatro fondos con estelas, espectro de ritmo, rebote,
partículas, cuatro transiciones, todos los controles CRT y los easter eggs.
Los efectos usan shaders propios de Qt, por lo que no son idénticos píxel a píxel
a los de shaders.com. El espectro representa el ritmo; no es un FFT musical.

En **Guardar**, guarda el aspecto por canción, artista o álbum. Se aplica en ese
orden de prioridad y se restaura la configuración habitual al salir. El bloqueo
global desactiva los presets y el tema automático de Joji. El modo Fiesta/Fluido
elegido manualmente tiene prioridad. Puedes ver, borrar, copiar e importar presets
JSON, incluidos los antiguos (`fv_presets`) de la web. No se lee automáticamente
el almacenamiento privado del navegador.

**Guardar → Estilos por género** ofrece tres recetas listas para aplicar:

| Estilo | Aspecto |
| --- | --- |
| Salsa · Candela | Fiesta al 90%, atardecer cálido, Space Grotesk, rebote, partículas y transición vinilo |
| Bachata · Seda | Fluido rosa/violeta, pulso al 45%, Georgia, estelas y transición obturador; sin partículas |
| Reguetón · Neón | Fiesta al 100%, neón, Impact, espectro, rebote, partículas y transición de color |

Se aplican con un botón y se guardan como configuración habitual. No cambian
la clasificación de la canción, la sensibilidad, la fuente del ritmo, los tiempos,
el tamaño de letra ni el movimiento reducido. La elección es manual; no hay un
cambio automático de estilo al detectar un género. Los presets por música
existentes mantienen su prioridad al entrar en otra canción. El modo manual
Fiesta/Fluido sigue siendo global, como en el resto de los presets.

Atajos: **F** cambia Fiesta/Fluido, **Q** muestra el QR, **A** o **,** abre Ajustes,
**F11** alterna pantalla completa y **Esc** cierra Ajustes/sale de pantalla completa.
Los atajos de letras se desactivan al editar ajustes. El QR abre la canción actual
en Spotify, igual que la web: no hay un servicio de votación detrás.

La desconexión borra la sesión local sin reimportarla al siguiente inicio.
Restablecer configuración conserva los presets y las calibraciones por canción.
La edición web y su túnel para móviles siguen disponibles por separado con
`python fiesta_launcher.py --web` y `host_public.cmd`; la ventana Qt no es un
servidor web ni un reproductor de Spotify.

Eliminar el navegador no elimina el coste de la GPU, la resolución ni las
latencias de Spotify. La textura de efectos se limita a 1920 píxeles de ancho y
el control de resolución permite reducirla. La calidad automática baja tras dos
segundos por debajo de 45 FPS y recupera tras diez por encima de 55 FPS, incluso
si solo permanece abierta la ventana traducida. No se garantiza una tasa de FPS.

## Construir desde el código

Requiere Windows de 64 bits y Python 3.11 o posterior:

```powershell
.\setup_desktop.ps1
.\build_desktop.ps1
.\.venv-desktop\Scripts\python.exe fiesta_desktop.py
```

Si PowerShell bloquea scripts, ejecútalos con
`powershell -NoProfile -ExecutionPolicy Bypass -File build_desktop.ps1`
(igual para setup/install); solo afecta a ese proceso. `install_desktop.ps1`
copia el paquete a `%LOCALAPPDATA%/Programs/FIESTA-Native` y crea accesos directos
**FIESTA Native**, sin autoarranque ni permisos de administrador.

El build compila GLSL a paquetes Qt con HLSL para Direct3D, convierte la fuente
WOFF/WOFF2 existentes a TTF y crea un paquete PyInstaller onedir. Las dependencias están
fijadas en `requirements-desktop.txt`; no se distribuyen los entornos de desarrollo.

Verificación aislada, sin Spotify, red ni captura:

```powershell
.\dist\FIESTA\FIESTA.exe --smoke-test --smoke-output native-smoke.png
.\dist\FIESTA\FIESTA.exe --smoke-test --smoke-showcase --smoke-output native-effects.png
.\.venv-desktop\Scripts\python.exe -m unittest tests.test_desktop_timing tests.test_desktop_preferences
```

La primera orden abre dos ventanas durante cuatro segundos y guarda una imagen
y un informe JSON con API gráfica, frames y avisos. Es una comprobación funcional,
no una comparación de rendimiento con el navegador.
`--smoke-settings --smoke-tab 3` muestra Guardar y `--smoke-lens 100` fuerza la
curvatura máxima. `--smoke-showcase` ejercita las cuatro transiciones, partículas,
rebote, espectro y QR sin modificar tus preferencias guardadas.

Qt/PySide se distribuyen como bibliotecas dinámicas reemplazables. Sus licencias
y las de otras dependencias están en `_internal/licenses`; consulta también
`THIRD_PARTY_NOTICES.md`. Para redistribuir, conserva esa carpeta y los avisos.
