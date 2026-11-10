# FIESTA — changelog

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
