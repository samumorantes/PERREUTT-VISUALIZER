# FIESTA — changelog

## En desarrollo — 2026-11-15
- **Estilos nativos por género:** Salsa · Candela (cálido y dinámico),
  Bachata · Seda (fluido rosa/violeta) y Reguetón · Neón (flashes intensos).
  Tarjetas con paleta y aplicación directa en Ajustes → Guardar; conservan
  sensibilidad, sincronización, calibración y preferencias de accesibilidad.
- **Funciones web recuperadas en la aplicación nativa:** temas, seis fuentes,
  tamaño/frases/espaciado/mayúsculas, borde y sombra, contraste por zonas,
  paletas de fiesta y portada/manual, estelas, espectro de ritmo, rebote,
  partículas y cuatro transiciones. Presets canción/artista/álbum con bloqueo
  global, restauración de la base e importación JSON; QR de la canción,
  easter eggs y tema Joji; controles CRT completos y calidad automática.
  Ajustes organizados en Letra/Ritmo/CRT/Guardar, desconexión y restablecimiento.
  Inventario y diferencias de renderizado en desktop/FEATURE_PARITY.md.
- **Correcciones visuales nativas:** lente que conserva los límites de la imagen
  sin repetir píxeles del borde; progreso separado del borde para evitar la banda
  gris estirada. Ajustes con cristal desenfocado, reflejos y pestañas Letra/Ritmo/
  CRT/Guardar; controles y botones coherentes con el panel.
- **Flashes nativos más sensibles e intensos:** umbral inicial 1,75, fuerza 85%
  y filtro interno de candidatos reducido a 1,25 para admitir ataques suaves.
  El control de umbral explica que bajarlo aumenta la sensibilidad.
- **Edición nativa Windows:** Qt Quick con Direct3D 11, sin navegador/WebView.
  Render GPU de fondos, flashes y cristal curvado con letra y cabecera; Spotify,
  traducción y WASAPI en hilos de trabajo. Segunda ventana nativa con reloj
  compartido, ajustes persistentes y paquete FIESTA.exe con Python incluido.
  Build reproducible, prueba gráfica aislada y lanzador nativo por defecto.
  Uso, construcción y límites de integración detallados en DESKTOP.md.
- **Umbral de flashes más alto:** de 3 a 4,5 en percusión general y de 6 a 7,5
  en acentos fuertes, para reducir pulsos por ataques débiles.
- **Percusión local sin micrófono:** captura WASAPI compartida, transitorios por
  bandas y eventos SSE; silencio sin flashes inventados, descarte de eventos
  antiguos al pausar, buscar o cambiar de canción y soporte de movimiento reducido.
- **Género por canción:** sugerencias desde etiquetas de artistas, perfil mixto o
  desconocido y corrección manual persistente. Perfiles de salsa, bachata, reguetón
  y percusión general; el género no impone BPM, compás ni una clave artificial.
- BPM por periodicidad con ambigüedad mitad/doble indicada; acentos fuertes y
  posibles drops por energía claramente separados de compases/drops confirmados.
- Dependencias de audio opcionales en un entorno local, instalación reproducible,
  estudio con fuentes y pruebas de señales sintéticas y del programador de flashes.

## En desarrollo — 2026-11-14
- **La UI también se curva**: portada, título, cola y LED se quedan junto al
  cristal; el margen de seguridad crecía con la lente y los empujaba al centro,
  donde la deformación es mínima. Ahora acompañan la curvatura del tubo y solo
  se separan un poco en intensidades extremas. Portada, título, artista, cola,
  fuente y LED son un poco más grandes para leerse mejor en pantalla grande.
- **Viñeta curva**: el oscurecimiento del cristal deja de ser un rectángulo.
  Una elipse CSS dentro de la lente sustituye al nodo `Vignette` de WebGPU y al
  `box-shadow` interior del CRT; el color llega hasta el bisel en los lados y
  la sombra se concentra en las esquinas, siguiendo la curva del tubo y sin
  líneas rectas. Se conserva el control Viñeta/curvatura y funciona también con
  `?legacyEffects`.
- **Sincronización de flashes**: reloj monotónico con compensación del tiempo
  de consulta, correcciones pequeñas graduales y reposicionamiento al hacer seek.
  Las letras/compases ya no retrasan el reloj. La envolvente sigue el tiempo
  musical; se descartan golpes atrasados en vez de reproducirlos en ráfaga.
- **Calibración por canción** en Ritmo: marcar 4–8 beats para ajustar BPM/fase,
  adelanto/retraso de ±500 ms y restauración. Se comparte entre las dos ventanas.
  Se distingue ritmo real/estimado/calibrado y se eliminan los falsos drops
  cada 32 beats cuando Spotify no entrega análisis.
- **Doble pantalla con traducción**: reemplaza el interruptor de subtítulos
  traducidos por una segunda ventana con la traducción como letra principal.
  Idiomas de origen/destino en Ajustes → Letra, ventana reutilizable y botón
  de pantalla completa. Comparte la posición de Spotify, prepara cinco frases
  cercanas, reutiliza resultados y descarta respuestas de frases/pistas viejas.
  Sincronización por frase; avisos ante ventanas bloqueadas o fallo de traducción.
- **Fiesta sobre negro**: ataque inmediato, caída exponencial y un intervalo
  completamente negro entre golpes. Caída suave durante el 94% del beat,
  con un breve pico sostenido y solo el 6% en negro; fuerza configurable,
  texto blanco, sin colas de temporizadores.
  Pausa, cambio a fluido y movimiento reducido apagan los pulsos.
- **Calidad automática a 60 Hz**: ya no degrada efectos por no alcanzar 100 fps;
  baja tras 2 s por debajo de 45 fps y recupera tras 10 s por encima de 55 fps.
- **shaders.com 4.0.7 (MIT), servido localmente**: fondos FlowingGradient,
  Swirl, Plasma y Aurora; TimeTrail para estelas; CRTScreen y FilmGrain para
  la textura del cristal; RandomBars, BarnDoors y NoiseDissolve
  para transiciones, con SolidColor y Group como capas de composición.
- Selector de fondo en Ritmo, incluido en presets; paleta de portada/manual,
  velocidad por tempo y deformación/brillo por beat. Resolución adaptativa,
  pausa al ocultar la pestaña y respeto al movimiento reducido.
- Alternativa Canvas/CSS ante WebGPU ausente o fallos de inicialización y con
  calidad mínima. Se mantienen la lente SVG para curvar el DOM, el vinilo,
  espectro, partículas y barrido de refresco.
- Bundle reproducible con npm/esbuild; Python sirve únicamente la ruta exacta
  del archivo público. Sin CDN, cuenta de shaders.com ni telemetría.

## v2.4 "TURBO²" — 2026-11-11
- **Cristal completo y lente compartida**: fondo, letra, CRT, portada, título,
  avisos, cola y LED comparten el filtro de ojo de pez. La pantalla llena el
  hueco del PNG con 2 px de solape bajo el bisel, sin el margen negro interior.
  El margen de seguridad se aplica solo a la UI; el cristal permanece fijo
  respecto al marco incluso al desactivar la lente. Los ajustes siguen fuera.
- **Fuera de pantalla no se hace polling**: `tick()` se detiene con la pestaña
  oculta y vuelve a sincronizar al recuperar visibilidad (antes seguían 4
  peticiones/s a `/api/sync`, más `/api/state` si fallaba).
- **Backoff ante servidor caído**: los reintentos pasan de 250 ms a 500 ms,
  1 s, 2 s y 4 s, en vez de martillar el servidor cada cuarto de segundo.
- **Presets en memoria**: `loadPresets()` cachea el JSON de localStorage; el
  tick ya no reparsea la tienda 4 veces por segundo.
- **Caché de ajuste de letra**: `fitLyric` reutiliza el tamaño ya calculado
  para texto/caja/fuente iguales (coros, resize y repintados), con límite de
  96 entradas y limpieza al cambiar fuente o viewport.
- **Accesibilidad**: soporte de `prefers-reduced-motion`, foco visible por
  teclado, panel con `role="dialog"`/`aria-hidden`, `aria-expanded` en el
  engranaje, `aria-pressed` en fiesta/fluido y cierre con Escape.
- **Servidor**: cabeceras `X-Content-Type-Options`, `X-Frame-Options` y
  `Referrer-Policy` en todas las respuestas; sigue pensado para loopback.
- La cola tampoco consulta `/api/queue` mientras la pestaña está oculta.
- **Panel de ajustes compacto y por pestañas**: 4 pestañas (Letra / Ritmo /
- CRT / Guardar) con cabecera fija y cuerpo con scroll propio, en vez de una
- columna con 9 secciones seguidas. Checkboxes de dos en dos, etiquetas cortas
- con tooltip, botones de preset en rejilla y pestaña recordada entre sesiones
- (`fv_tab`), con navegación por flechas y cierre con Escape/✕.
- Verificación: parseo del JS inline, `py_compile`, `git diff --check`, APIs
  reales y comprobación DOM en navegador.

## v2.3 "SYNC" — 2026-11-10
- Letras fieles con la **API de Spicy Lyrics** (el mismo catálogo TTML
  comunitario que usa la extensión de Spicetify): tiempos por sílaba/palabra,
  coros `Background` y jerarquía Syllable → Line → Static. Se activa con
  `spicy_key.txt` o `SPICYLYRICS_KEY`; sin clave todo sigue igual.
- **Karaoke real**: cada palabra/sílaba se rellena con su `StartTime/EndTime`
  (capas base/relleno con `clip-path`), sin repartos uniformes.
- El cambio de frase ya no espera al poll de `/api/sync`: usa los tiempos
  exactos de la lista de frases y corrige la fase al entrar. Las frases
  repetidas (mismo texto) reinician el karaoke (antes no lo hacían).
- El tamaño de letra se ajusta en el MISMO frame que la frase nueva: antes
  `fitLyric` corría en el frame siguiente y al cambiar de palabra se veía un
  instante el tamaño de la frase anterior (micro-flicker).
- `split_phrases` corta por la duración REAL de cada palabra cuando la fuente
  trae tiempos (Spicy o LRC mejorado), no por la línea completa.
- `parse_lrc` entiende LRC mejorado (`<mm:ss.xx>` por palabra) además del LRC
  normal, así que también mejora las canciones de LRCLIB con ese formato.
- `/healthz` informa `spicy: true/false` para saber si la clave está cargada.
- Debugging intensivo de la sincronización:
  - La letra anterior se congela durante el cambio de pista (no avanza con la
    posición de la canción nueva) y se descongela aunque falle el fetch.
  - La traducción async usa un contador de generación: no puede pisar una
    frase posterior, aunque el texto se repita.
  - En LRC mejorado, la última palabra se rellena hasta el inicio de la línea
    siguiente (tope 2,5 s): antes se quedaba "muerta" a los 0,35 s.
  - El fallback de línea cruda usa `track|idx|t|texto`; las frases repetidas
    reinician el karaoke.
  - `#lyrics` se hace visible antes de `fitLyric` y `hideMsg` ya no muestra
    un contenedor vacío ni superpone «NO LYRICS». Un seek antes de la primera
    línea limpia la frase futura en vez de dejarla en pantalla.
  - En móvil, el título usa solo el nombre real (sin los `♪` decorativos), se
    limita a 2 líneas y deja margen lateral. Los espacios entre palabras son
    texto real con `word-spacing`: al partirse una frase, el espacio del salto
    ya no cuenta como ancho y las líneas quedan centradas de verdad.
  - Transiciones: se cancelan los timers de la transición anterior antes de
    arrancar otra (obturador, vinilo, flash y TV ya no se pisan); las capas se
    ocultan 50 ms después de terminar su animación; `song-flash` reinicia y
    termina en opacidad 1 sin salto; el pulso de color limpia su reset; y
    `screenDrift` vuelve a animar la inclinación cuando la lente está apagada.
  - Al volver a la pestaña se reaplica la disposición compacta/vertical y se
    reajusta la letra si el tamaño de la ventana cambió mientras estaba oculta.
  - Ojo de pez: el mapa de barril ahora usa coordenadas en píxeles reales
    (corrige la elipse en pantallas no cuadradas), 160x160 con menos blur y
    muestrea siempre dentro del origen, sin bordes negros. La fórmula inversa
    amplía el centro y deja el borde quieto.
  - Transiciones: `renderState()` ya no vuelve a lanzar la transición que
    `tick()` inició al detectar el cambio de pista; se elimina el doble corte
    de obturador/vinilo/TV al cargar el estado nuevo.
  - Mueble de TV: `#screen` se reduce `6vmin` dentro del hueco para que el
    bisel curvo no tape la portada, el título ni la letra. En compacto y sin
    mueble la pantalla sigue ocupando todo el viewport.
  - El mueble solo se usa cuando el viewport tiene al menos el ratio real del
    PNG (1.52); antes el rango 1.45–1.52 recortaba los lados de la UI.

## v2.2 "LAB" — 2026-11-09
- Fusión completa de **FIESTA LAB** dentro del visualizador: mueble de TV vintage
  (`tv-frame-clean.png`), lente SVG (ojo de pez real por píxel), temas completos,
  presets por canción/artista/álbum, paleta manual, espectro CRT, partículas en
  los drops, rebote al beat, estelas, QR para votar, traducción de letras,
  contraste inteligente por zonas, contador de FPS y reglas por canción.
- Rendimiento (>100 fps):
  - Los tres bucles `requestAnimationFrame` (render, fluido y partículas) se
    funden en **uno solo** (`rafLoop`): menos overhead y orden de pintado fijo.
  - Calidad adaptativa con histéresis: si no se sostienen 100 fps baja sola la
    lente, las estelas, la resolución del fluido y las partículas; se recupera
    al superar 110 fps. Interruptor «Calidad automática» en el panel.
  - El fluido usa delta real (misma velocidad a 60 y a 120 Hz) y resolución
    escalable; las partículas se dibujan en un canvas a media resolución y ya
    no lanzan su propio bucle.
  - Las partículas del drop salen del centro real del canvas (antes se lanzaban
    desde `innerWidth/2` sobre un canvas a media resolución y salían torcidas).
  - Contraste del texto sin leer píxeles del canvas, barra de progreso y rebote
    limitados a 10/20 Hz, y `applyLens` no reescribe el filtro si no cambia.
  - La lente ya no filtra las capas animadas (fluido, ruido, refresh): pasan a
    capas hermanas, así el `feDisplacementMap` se reaprovecha entre líneas.
  - Fluido en canvas GPU (sin `willReadFrequently`), paleta y gradientes
    cacheados y blobs dibujados como sprites (`drawImage`).
  - Ojo de pez reactivado una vez si un preset antiguo lo había dejado apagado.
  - Medido a 2560×1440 con fluido, lente, estelas y 90 partículas: 118 → 185 fps.
- Servidor:
  - `GET /tv-frame-clean.png` (cacheado en memoria, `max-age=86400`).
  - `/api/state?mw=1` y `?force=1` (recarga sin caché) para el nuevo frontend;
    `mw` se sanea a 1..8 en todos los caminos.
- El selector rápido 🎉/🌊 vuelve a estar (el LAB lo había sustituido por la
  tecla F) y convive con los ajustes.

## v2.1 "TIDY" — 2026-11-09
- Servidor:
  - Cachés de letras, análisis y portadas ahora son acotadas (antes `_bounded_cache_set`
    existía pero no se usaba: crecían sin límite en sesiones largas).
  - `token.json` se lee una vez y se cachea en memoria (antes, disco en cada poll);
    el refresh del token va bajo lock y la escritura es atómica.
  - `/api/sync` ya no se solapa entre pestañas: un solo refresh a la vez y el resto
    extrapola; un 429 de Spotify respeta 20 min de pausa en vez de reintentar cada 1,5 s.
  - Estado de login PKCE con caducidad (10 min) y limpieza: no se acumulan si se reintenta.
  - Presupuesto de API thread-safe y rutas del servidor separadas por endpoint
    (antes un único `do_GET` de 300 líneas).
  - Nuevo `/healthz` (latido sin gastar cuota) y puerto configurable con `FIESTA_PORT`.
  - Logs OAuth sin código ni cuerpos de respuesta; se activan con `FIESTA_DEBUG=1`.
- Lanzador: espera a `/healthz`, guarda la salida del server en `fiesta.log` y avisa
  con un diálogo si el servidor no arranca (antes abría una pestaña muerta).
- Frontend:
  - Corregido el polling: un tick lento podía duplicar cadenas de `tick()` y multiplicar
    las peticiones al servidor de forma permanente.
  - Contraste real en paletas HSL (se leían como si fueran RGB).
  - Sin sesión ya no se consulta la cola cada 15 s.
  - Una sola función `showLine()` para pintar letra + easter eggs (antes 3 copias).

## v2.0 "TURBO" — 2026-10-23
- Corrección de bugs críticos:
  - Fix crash en `showMsg`/`hideMsg` (`$("#msg")` con selector incorrecto).
  - Fix extracción de tempo en análisis de Spotify (`track` vs `tracks`).
  - Preservación de coros/voces secundarias (`back`) al trocear frases (`split_phrases`).
  - Ruta de iconos y scripts dinámica (elimina rutas absolutas fijas).
- Rendimiento y optimización:
  - Cache en memoria reutilizable para análisis de canvas y contraste (cero fuga de memoria).
  - Eliminado layout thrashing recurrente en fisheye y pintado de frames.
  - Caches del servidor acotados para evitar acumulación infinita de memoria en sesiones largas.
  - Caché de fuentes y favicon en memoria en el servidor con encabezados HTTP óptimos.
- Seguridad y privacidad:
  - Eliminado registro de código OAuth en texto plano en la consola.
  - Sanitización en transiciones de portada de vinilo contra inyecciones HTML.
  - Ámbito de permisos recortado al mínimo necesario (`user-read-email` removido).
- Interfaz y accesibilidad:
  - Enlace al favicon `fiesta.ico` en HTML.
  - Soporte de tecla Escape para cerrar panel de ajustes.
  - Etiquetas accesibles en botones de modo y controles.
  - Corrección de selector de transición URL (`flashcolor`) y respeto a preferencias de timing.

## v1.3 "CONFIG" — 2026-08-23
- Panel de configuración completo y funcional: 6 fuentes, 6 paletas, fuerza del flash,
  pulso de color vs flash blanco, grosor/sombra de letra, transición "flash de color"
- Botón "Restablecer configuración" con sincronización instantánea del panel
- Fix crítico: parpadeo de letra (dos fuentes peleándose) → una sola autoridad + freno anti-flip
- Fix: ghosting del texto (fisheye suavizado rotY -14°→-4°)
- Fix: contraste con histéresis anti-flicker
- Instalador end-to-end: install.ps1 (accesos directos con icono, auto-arranque, desinstalador)

### v1.2 "CHILL" — 2026-08-22
- Modo chill autodetectado (BPM/energía de letra <2.5 sílabas/s): fluido con paleta de portada
- Fluido interactivo canvas: blobs que respiran al BPM y rotan color por beat
- Ticker de cola ("A CONTINUACIÓN") + auto-hide UI 5s
- Selector rápido fiesta/fluido flotante

### v1.1 "SYNC" — 2026-08-22
- Easter egg EOO solo efectos (letra intacta), flip B/N puro
- Título 7s antes de la letra
- Fallback anti NO-LYRICS (nunca queda sin letra)
- Limpieza general del código

### BETA 1.0 "ARCADE" — 2026-08-19
- Letra sincronizada en tiempo real, RGB por beat, estética CRT arcade
- LED de estado SYNC/WAIT/OFFLINE, sync ante seeks instantáneo
- Transición TV al cambiar canción
