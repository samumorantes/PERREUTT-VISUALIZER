# Mueble PERRE’UTT — versión 1

Composición raster a partir del marco existente y los logos originales de la
carpeta `Desktop/PERREUTT` facilitada por el usuario. No es una generación por IA
ni utiliza una API de imágenes.

Dirección: negro grafito, metal frío, reflejos magenta/cian e identidad orbital
de PERRE’UTT. Tres adhesivos: holográfico, magenta sobre negro y tinta negra sobre
vinilo blanco. Las letras y el símbolo proceden de los originales, sin redibujar
ni sustituir la tipografía. El mueble conserva su textura, proporciones y canal
alfa original para mantener intacto el espacio del visualizador.

## Archivos

- `tv-frame-perreutt-v1.png`: marco consumido por FIESTA Native, 1493 × 983 RGBA.
- `references/perreutt-logo.svg`: copia exacta de `PERREUTT.svg`.
- `references/perreutt-chrome.png`: copia exacta de `Logo chromé irisé PERRE’UTT.png`.
- `build_frame.py`: composición reproducible con NumPy y PySide6 del entorno nativo.

Desde la raíz: `.venv-desktop/Scripts/python.exe desktop/artwork/build_frame.py`.
El marco anterior `tv-frame-clean.png` se conserva. No cambia la edición web ni
se sustituye el instalador 2.5.0 guardado en el historial del repositorio.
