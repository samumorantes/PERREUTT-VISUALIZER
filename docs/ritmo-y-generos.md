# Ritmo y percusión de FIESTA

Estudio aplicado, 15 de noviembre de 2026. Un género no determina el BPM, la
posición del primer golpe ni los drops de una grabación. Las cifras de tempo
de otras canciones no sirven para alinear la canción actual.

## Compás, pasos y percusión

| Género | Organización habitual | Qué escuchar para los flashes |
| --- | --- | --- |
| Salsa | Pulso binario, representado en 4/4 o 2/2 según la transcripción. Clave de cinco ataques organizada en dos lados: 3–2 o 2–3. | Congas, timbales, campana y bajo sincopado. Tres golpes de un lado de la clave **no** significan compás de tres tiempos. La clave puede no sonar explícitamente. |
| Bachata | 4/4 habitual; el baile suele agrupar ocho tiempos. | Bongó, güira y bajo. El tap del cuarto/ocho del baile no prueba que allí esté el ataque más intenso de la mezcla. Puede incorporar secciones de merengue. |
| Reguetón | 4/4 habitual, dembow sincopado; influencia de tresillo 3+3+2 en subdivisiones. | Ataques graves y caja/palito. Repartir cuatro flashes iguales elimina los contratiempos del patrón. Hay variaciones y fusiones. |
| Merengue | Binario, habitualmente escrito en 2/4. | Tambora y güira; perfil de transitorios, sin generar un compás automático. |
| Cumbia | Binario, con instrumentación y acentos diferentes entre variantes. | Ataques y contratiempos realmente presentes. |
| Pop, rock, electrónica, mixto | No se asume un compás universal. | Perfil general o preferencia por graves/caja; no se impone un BPM. |

Las tres primeras tradiciones son el foco de esta revisión; los otros perfiles
son ajustes generales de ingeniería, no un estudio exhaustivo de sus variantes.
Las ponderaciones de frecuencias no identifican instrumentos separados ni son
un clasificador musical entrenado.

## Fuentes consultadas

- [Clave: tipos, notación y orientación 3–2/2–3](https://en.wikipedia.org/wiki/Clave_(rhythm)).
  Distingue la clave de cinco golpes de su notación en 4/4, 2/4 o 2/2 y sus variantes ternarias.
- [Bachata: instrumentación y fusiones](https://en.wikipedia.org/wiki/Bachata_(music)).
  Describe requinto, segunda, bajo, bongó, güira y el cambio a tambora en secciones de merengue.
- [Bachata: baile](https://en.wikipedia.org/wiki/Bachata_(dance)).
  El conteo de pasos es una referencia de baile, no un mapa de ataques de audio.
- [Reguetón: ritmo](https://en.wikipedia.org/wiki/Reggaeton#Rhythm).
  Describe dembow, sus componentes de percusión, tresillo y base en 4/4.
- [Microsoft: WASAPI loopback](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording).
  Permite capturar la mezcla de un dispositivo de salida; no requiere micrófono.
- [Spotify: Get Artist](https://developer.spotify.com/documentation/web-api/reference/get-an-artist).
  Los géneros corresponden al artista y pueden faltar; no son etiquetas verificadas de cada canción.
- [PyAudioWPatch](https://pypi.org/project/PyAudioWPatch/): integración local con WASAPI.

## Implementación y límites

1. **Clasificación por canción:** consulta las etiquetas de hasta tres artistas,
   con caché, y propone salsa, bachata, reguetón u otro perfil. Mezclas de
   categorías específicas se muestran como mixtas; sin evidencia queda «Sin
   clasificar». Una corrección manual se guarda por ID de canción y se comparte
   entre las ventanas del mismo origen. No se infiere el género solo por BPM,
   nombre del artista o título. Las sugerencias no equivalen a reconocimiento
   acústico de género.
2. **Audio local:** captura exclusivamente el loopback de la salida predeterminada
   de Windows. No abre entradas de micrófono, guarda grabaciones ni envía audio
   a Internet. Otros sonidos que salgan por ese dispositivo también pueden
   generar transitorios. Spotify Connect en otro equipo no llega a esta captura.
3. **Golpes:** flujo espectral positivo en tres bandas (35–220, 220–2500 y
   2500–10000 Hz), umbral adaptativo, puerta de silencio y separación mínima.
   El perfil de género pondera bandas, pero no recoloca golpes ni inventa
   notas faltantes. Ataques de voz, bajo o guitarra pueden confundirse con
   percusión: no hay separación de fuentes ni reconocimiento instrumental.
4. **BPM:** autocorrelación sobre hasta ocho segundos, actualizada cada medio
   segundo tras cuatro segundos de contexto; rango de búsqueda 55–220 BPM.
   Es una estimación de periodicidad, con posible ambigüedad mitad/doble. No se
   usa para generar golpes en vivo, solo para informar y ajustar la duración
   del flash. No detectamos automáticamente el primer tiempo del compás.
   El disparo visual exige una puntuación ponderada de al menos 4,5; el modo
   de acentos fuertes exige 7,5. Estos umbrales reducen la respuesta a ataques
   débiles y no representan decibelios ni probabilidades.
5. **Transporte:** SSE comparte una captura entre ventanas. Se descartan golpes
   antiguos y colas al pausar, cambiar de pista, buscar o volver a una pestaña.
   En directo, «Cada compás» se convierte explícitamente en «Acentos fuertes»;
   «Solo secciones» pasa a «Posibles drops». No fingimos identificar downbeats.
6. **Drops:** caída sostenida de energía y regreso con un ataque grave, con
   separación de ocho segundos. Son **candidatos**, no drops confirmados.
   No se inventan cada 32 golpes. El detector necesita contexto continuo;
   no interpreta la estructura completa de una canción.
7. **Latencia:** los eventos usan marcas de captura; el flash comienza en la
   fase correspondiente al tiempo ya transcurrido. La latencia del dispositivo,
   del navegador, del monitor y de la red no desaparece. La cifra de captura
   mostrada no mide la sincronización acústica de extremo a extremo. Un retraso
   negativo se puede programar; un adelanto positivo solo se aplica al mapa,
   porque no podemos anticipar audio que aún no se ha reproducido.

En silencio o sin captura, el modo de percusión no dispara una cuadrícula de
respaldo. Se puede elegir explícitamente «Mapa de Spotify / calibración manual»;
su estimación de 120 BPM sigue claramente identificada como estimación.

## Validación reproducible

`python -m unittest discover -s tests -p test_percussion.py -v` comprueba silencio,
tono sostenido, ataques conocidos a 90/120/150 BPM, síncopas, estéreo con fase
invertida y clasificación con etiquetas ambiguas. Son señales sintéticas:
no prueban exactitud en todas las grabaciones de salsa, bachata o reguetón.

La validación de la interfaz comprueba descarte de colas, pausa, seek y retraso
manual. Para medir precisión musical real hace falta comparar canciones de
referencia con marcas de percusión revisadas y medir la latencia física de salida.
