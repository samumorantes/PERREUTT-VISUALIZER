# Native onedir build: replaceable Qt shared libraries, no Chromium/WebEngine.
from pathlib import Path
from importlib.metadata import distribution
import sys
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
datas = [(str(root / 'desktop' / '*.qml'), 'desktop'),
         (str(root / 'desktop' / '*.ttf'), 'desktop'),
         (str(root / 'desktop' / 'artwork' / 'tv-frame-perreutt-v1.png'), 'desktop/artwork'),
         (str(root / 'desktop' / 'shaders' / '*.qsb'), 'desktop/shaders'),
         (str(root / 'desktop' / 'licenses' / '*.txt'), 'licenses'),
         (str(root / 'fonts' / 'user' / 'pizzadudedotdk.txt'), 'licenses/ArcadeClassic'),
         (str(root / 'tv-frame-clean.png'), '.'), (str(root / 'fiesta.ico'), '.'),
         (str(root / 'THIRD_PARTY_NOTICES.md'), '.'),
         (str(root / 'DESKTOP.md'), '.'),
         (str(root / 'docs' / 'PLATFORMS.md'), 'docs'),
         (str(root / 'desktop' / 'FEATURE_PARITY.md'), 'desktop')]
if sys.platform != 'win32':
    # SoundCard loads CFFI declarations from header files at runtime.
    datas += collect_data_files('soundcard')
packages = ['PySide6', 'PySide6-Essentials', 'PySide6-Addons', 'shiboken6', 'numpy', 'pyinstaller', 'qrcode']
packages += ['PyAudioWPatch'] if sys.platform == 'win32' else ['SoundCard', 'cffi', 'pycparser']
for package in packages:
    dist = distribution(package)
    for file in dist.files or []:
        if any(part.lower() in ('licenses', 'license', 'copying') for part in file.parts) or file.name.lower().startswith(('license', 'copying', 'notice')):
            path = Path(dist.locate_file(file))
            if path.is_file():
                datas.append((str(path), 'licenses/' + package + '/' + str(file.parent).replace('..', '_')))

a = Analysis(['fiesta_desktop.py'], pathex=[str(root)], binaries=[], datas=datas,
             hiddenimports=['PySide6.QtQuickControls2', 'PySide6.QtNetwork'],
             excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineQuick', 'PySide6.QtWebEngineWidgets',
                       'PySide6.QtWebView', 'PySide6.QtWebChannel', 'tkinter', 'fontTools', 'pip'],
             noarchive=False)
# Qt's generic QML hook collects optional modules. Keep only the imports used by
# this UI, and the Basic controls style. Nothing here uses QtWidgets/WebEngine.
def needed(entry):
    name = entry[0].replace('\\', '/')
    low = name.lower()
    if any(word in low for word in ('webengine', 'webview', 'qtwebchannel', 'qt6web', 'qtwebsockets')):
        return False
    if name.startswith('PySide6/Qt6') and name.endswith('.dll'):
        module = Path(name).stem[3:]
        if module not in {'Core', 'Gui', 'Network', 'Concurrent', 'Qml', 'QmlCore', 'QmlMeta',
                          'QmlModels', 'QmlNetwork', 'QmlWorkerScript', 'QmlLocalStorage', 'QmlXmlListModel',
                          'Quick', 'QuickControls2', 'QuickControls2Basic', 'QuickControls2BasicStyleImpl',
                          'QuickControls2Impl', 'QuickTemplates2', 'QuickLayouts', 'OpenGL',
                          'OpenGLWidgets', 'Widgets', 'Svg', 'Pdf', 'Sql', 'ShaderTools'}:
            return False
    if name.startswith('PySide6/plugins/'):
        category = name[len('PySide6/plugins/'):].split('/')[0]
        if category not in ('platforms', 'imageformats', 'iconengines', 'tls', 'networkinformation', 'styles'):
            return False
    prefix = 'PySide6/Qt/qml/' if name.startswith('PySide6/Qt/qml/') else 'PySide6/qml/'
    if name.startswith(prefix):
        rel = name[len(prefix):]
        if not rel.startswith(('QtQuick/', 'QtQml/')):
            return False
        if rel.startswith('QtQuick/Controls/'):
            sub = rel[len('QtQuick/Controls/'):].split('/')[0]
            if '/' in rel[len('QtQuick/Controls/'):] and sub not in ('Basic', 'impl'):
                return False
        if rel.startswith('QtQuick/'):
            sub = rel[len('QtQuick/'):].split('/')[0]
            if '/' in rel[len('QtQuick/'):] and sub not in ('Controls', 'Templates', 'Window', 'Layouts'):
                return False
    return True
a.datas = [entry for entry in a.datas if needed(entry)]
a.binaries = [entry for entry in a.binaries if needed(entry)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='FIESTA', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon=str(root / ('desktop/fiesta.icns' if sys.platform == 'darwin' else 'fiesta.ico')))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='FIESTA')
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='FIESTA.app', icon=str(root / 'desktop/fiesta.icns'),
                 bundle_identifier='org.perreutt.fiesta', version='2.6.0',
                 info_plist={'NSHighResolutionCapable': True,
                             'NSMicrophoneUsageDescription': 'FIESTA analiza la salida virtual BlackHole para sincronizar los efectos. No selecciona el micrófono físico.',
                             'LSApplicationCategoryType': 'public.app-category.music'})
