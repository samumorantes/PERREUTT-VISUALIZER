# Funciones del visualizador web en FIESTA Native

Inventario contrastado con los controles y comportamientos de `index.html`.
La aplicación dibuja con Qt Quick/Direct3D 11; no incorpora un navegador.

| Función web | Equivalente nativo |
| --- | --- |
| Spotify, estado, pausa, búsqueda, cambio de canción | Backend compartido, reloj monotónico y descarte de pulsos antiguos |
| Letras Spicy/Spotify/LRCLIB/lyrics.ovh, coros y respaldo | Mismo backend; karaoke por palabra/sílaba, coros y título inicial de 7 s |
| 1–4 palabras por frase | Reagrupación que conserva los tiempos de las sílabas |
| Temas Clásico, Vaporwave, Matrix, SNES | Letra → Tema completo; aplica fuente, paleta y CRT |
| Arcade, Space Grotesk, Impact, Courier, Georgia, sistema | Letra → Tipografía; dos fuentes locales empaquetadas |
| Tamaño 3–16, espacio 0–3, mayúsculas, borde 0–6, sombra | Controles de Letra, ajuste de tamaño al espacio disponible |
| Traducción como letra principal en otra pantalla | Segunda ventana Qt, mismo reloj, caché y anticipación de frases MyMemory |
| RGB, pastel, neón, atardecer, océano, blanco/negro | Ritmo → Paleta; flashes con caída exponencial y breve negro entre golpes |
| Pulso de color, flash blanco, intensidad | Controles independientes; movimiento reducido detiene pulsos |
| WASAPI, género, beats/acentos/drops, mapa, desfase y tap | Captura local sin micrófono, perfiles compartidos y calibración persistida por canción |
| Auto/Fiesta/Fluido, detectar baladas, botón rápido | Ritmo, botón superior y tecla F; modo manual tiene prioridad |
| Flow, Swirl, Plasma, Aurora | Cuatro fondos procedurales propios con cinco colores y cambio suave de paleta |
| Colores de portada y paleta manual/aleatoria | Extracción de imagen en un hilo; Guardar permite editar cinco colores hexadecimales |
| Estelas | Mezcla de muestras temporales del fluido en GPU, reducida en calidad baja |
| Espectro, rebote y partículas | 24 barras de ritmo, escala de letra al beat, hasta 60 partículas por drop |
| Contraste inteligente por zonas | Estimación local de luminancia de la paleta/fondo, con histéresis para cabecera, letra y pie |
| TV antigua, obturador, vinilo con portada, flash, ninguna | Ritmo → Transición y botón de prueba; se muestran con los datos de la nueva canción |
| Scanlines, flicker, inclinación, refresco, ojo de pez, TV | Controles individuales en CRT y botón todo/nada para efectos |
| Intensidades CRT, máscara, viñeta, ruido, lente | Shaders nativos; deformación que conserva los límites sin estirar píxeles |
| Presets canción/artista/álbum y override global | Guardar; prioridad canción → artista → álbum, retorno a configuración habitual |
| Ver/borrar presets, restaurar configuración | Lista, borrado individual/todos, JSON copiable/importable, confirmación de borrado total/restablecimiento |
| QR (llamado «votar» en la web) | Código local que abre la canción de Spotify; botón y tecla Q |
| Calidad automática | Baja tras 2 s a menos de 45 FPS, recupera tras 10 s a más de 55; escala de efectos y partículas |
| Cola, portada, título, artista, fuente y sincronización | Cabecera/pie dentro de la lente; cola con artista cada 15 s |
| Autoocultación, pantalla completa y atajos | 5 s de inactividad, F11/Esc, A/coma, F y Q; panel no se oculta mientras se usa |
| EOO y Perreo/Tra-tra/Chequéate la historia | Texto Impact, EOO creciente y alternancia blanco/negro; efectos CRT suspendidos durante la frase |
| Joji – Die For You | Vaporwave, paleta oscura y fluido automático; respeta bloqueo global y modo manual |
| Conectar/desconectar cuenta | OAuth en navegador del sistema; sesión local borrable sin reimportación involuntaria |
| Preferencias persistentes | Archivo nativo en LocalAppData; presets web JSON compatibles |

## Diferencias deliberadas y límites

- Los efectos tienen implementaciones Qt propias: estelas por muestreo temporal,
  partículas nativas y shaders GLSL/HLSL. No se promete equivalencia píxel a píxel
  con shaders.com, ni que la GPU deje de limitar el rendimiento.
- Como en la web, las barras son una visualización del ritmo, no un analizador FFT.
  Los drops de audio se estiman; las secciones de Spotify no implican siempre un
  drop. Sin análisis real, no se inventan cambios de sección cada 32 golpes.
- La traducción se alinea por frase, no por sílaba traducida. MyMemory depende de
  red, cuota y calidad externa. La segunda ventana conserva el texto traducido
  principal y no activa los easter eggs de las letras originales.
- El QR nunca tuvo un backend de votación: abre Spotify. Generarlo no envía datos
  a un servicio QR externo.
- La sesión de Spotify puede importarse una sola vez desde el checkout local.
  El almacenamiento del navegador no se lee automáticamente: los presets se
  importan pegando su JSON en Guardar. No se empaquetan credenciales.
- El acceso remoto por móvil continúa en la edición web y su túnel existente.
  No es una función del renderizador nativo. El lanzador permite `--web`.

## Verificación

Pruebas unitarias de reloj/programador, prioridad y persistencia de presets,
bloqueo global, restauración, importación validada, tema Joji y tiempos de sílabas.
Smoke gráfico aislado con dos ventanas, Direct3D, captura a lente 100 y panel
Guardar. El modo showcase ejercita transiciones, partículas, espectro, rebote
y generación QR. Estas comprobaciones no sustituyen una sesión con música real
ni prueban disponibilidad o cuota de los servicios externos.
