"""FIESTA native desktop. Qt Quick / Direct3D, without a browser engine."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11" if sys.platform == "win32" else "opengl")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QObject, QTimer, QUrl, QMetaObject, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QIcon, QFontDatabase
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow  # required by the packager
from shiboken6 import delete


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--smoke-output", default="native-smoke.png")
    parser.add_argument("--smoke-settings", action="store_true")
    parser.add_argument("--smoke-showcase", action="store_true")
    parser.add_argument("--smoke-tab", type=int, choices=range(4), default=0)
    parser.add_argument("--smoke-lens", type=float)
    parser.add_argument("--smoke-style", choices=('salsa','bachata','reggaeton'))
    parser.add_argument("--smoke-transition", choices=('tv','shutter','vinyl','flashcolor','none'))
    args = parser.parse_args()
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FIESTA-Native"
    data.mkdir(parents=True, exist_ok=True)
    # Migrate local credentials only at runtime; they are never build inputs.
    origin = Path(sys.executable).parent if getattr(sys, "frozen", False) else root
    if not args.smoke_test and not (data / '.credentials-imported').exists():
        candidates = [origin, origin.parent.parent]
        for name in ("config.json", "token.json", "spicy_key.txt"):
            if not (data / name).exists():
                for folder in candidates:
                    if (folder / "server.py").exists() and (folder / name).exists():
                        shutil.copy2(folder / name, data / name)
                        break
        (data / '.credentials-imported').touch()
    log_path = data / "desktop.log"
    if log_path.exists() and log_path.stat().st_size > 2_000_000:
        log_path.replace(data / "desktop.previous.log")
    log = log_path.open("a", encoding="utf-8", buffering=1)
    warnings = []

    def message(kind, context, text):
        log.write(f"{time.strftime('%H:%M:%S')} {kind.name}: {text}\n")
        if kind.name in ("QtWarningMsg", "QtCriticalMsg", "QtFatalMsg"):
            warnings.append(text)
        if args.smoke_test and sys.stderr:
            print(text, file=sys.stderr)

    qInstallMessageHandler(message)
    import server as backend
    backend.CONFIG = str(data / "config.json")
    backend.TOKENS = str(data / "token.json")
    backend.CLIENT_ID = "" if args.smoke_test else backend.load_client_id()
    # BASE is used for optional local API keys and OAuth assets, never rendering.
    backend.BASE = str(data)
    backend.SPICY_KEY = "" if args.smoke_test else backend._load_spicy_key()
    from desktop.controller import Controller
    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName("FIESTA Native")
    app.setOrganizationName("FIESTA")
    app.setWindowIcon(QIcon(str(root / "fiesta.ico")))
    family = "Consolas"
    font_id = QFontDatabase.addApplicationFont(str(root / "desktop" / "arcade.ttf"))
    if font_id >= 0:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
    grotesk_id = QFontDatabase.addApplicationFont(str(root / 'desktop' / 'grotesk.ttf'))
    grotesk = QFontDatabase.applicationFontFamilies(grotesk_id)[0] if grotesk_id >= 0 else 'Segoe UI'
    controller = Controller(data, smoke=args.smoke_test)
    if args.smoke_test and args.smoke_lens is not None:
        controller.setSetting("lens", args.smoke_lens)
    if args.smoke_test and args.smoke_style:
        controller.applyGenreStyle(args.smoke_style)
    engines = []
    windows = []
    second = None

    def new_window(translated=False):
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("bridge", controller)
        engine.rootContext().setContextProperty("arcadeFamily", family)
        engine.rootContext().setContextProperty("groteskFamily", grotesk)
        engine.setInitialProperties({"translationDisplay": translated})
        engine.load(QUrl.fromLocalFile(str(root / "desktop" / "Visualizer.qml")))
        if not engine.rootObjects():
            raise RuntimeError("No se pudo cargar la ventana nativa. Revisa " + str(log_path))
        window = engine.rootObjects()[0]
        engines.append(engine)
        windows.append(window)
        window.visibleChanged.connect(update_visibility)
        window.visibilityChanged.connect(update_visibility)
        update_visibility()
        return window

    def update_visibility(*_):
        reporter = next((w for w in windows if w.isVisible() and w.visibility() != QQuickWindow.Visibility.Minimized), None)
        for w in windows:
            w.setProperty('qualityReporter', w is reporter)
        active = any(w.isVisible() and w.visibility() != QQuickWindow.Visibility.Minimized for w in windows)
        controller.set_render_displays([w.property('displayId') for w in windows
                                       if w.isVisible() and w.visibility() != QQuickWindow.Visibility.Minimized])
        if controller.windows_active != active:
            controller.windows_active = active
            controller.scheduler.reset(time.monotonic())
            controller.clearPulse.emit()
        if second and not second.isVisible():
            controller.translationClosed()

    def open_second():
        nonlocal second
        if second is None:
            second = new_window(True)
        screens = app.screens()
        target = next((screen for screen in screens if screen != windows[0].screen()), None)
        if target:
            rect = target.availableGeometry()
            second.setScreen(target)
            second.setPosition(rect.x()+30, rect.y()+30)
            second.resize(min(1280,rect.width()-60), min(850,rect.height()-60))
        second.show()
        second.raise_()
        second.requestActivate()

    controller.openSecond.connect(open_second)
    app.aboutToQuit.connect(controller.shutdown)
    first = new_window()
    result_code = 0
    if args.smoke_test:
        started = time.monotonic()
        transition_checks = []
        if args.smoke_transition:
            controller.setSetting('transition', args.smoke_transition)
            controller.setSetting('reducedMotion', False)
            def audit_swap():
                if controller.view['title'] == 'NUEVA CANCIÓN' and not transition_checks:
                    transition_checks.append(all(w.findChild(QObject, 'trackCurtain').property('coverage') == 1
                                                 for w in windows if w.isVisible()))
            controller.viewChanged.connect(audit_swap)
            QTimer.singleShot(1000, lambda: controller.receive(dict(kind='loading', track='next-smoke')))
            def next_track():
                state = controller.smoke_state()
                state['track'].update(id='next-smoke', name='NUEVA CANCIÓN')
                state['progress_ms'] = 1000
                controller.receive(dict(kind='state', data=state, received_at=time.monotonic()))
            QTimer.singleShot(2000, next_track)
            def capture_cover():
                output = Path(args.smoke_output).resolve()
                output.parent.mkdir(parents=True, exist_ok=True)
                first.grabWindow().save(str(output.with_stem(output.stem+'-covered')))
            QTimer.singleShot(1650, capture_cover)
        if args.smoke_showcase:
            controller.setSetting('spectrum', True)
            controller.setSetting('beatBounce', True)
            controller.setSetting('mood', 'party')
            controller.setSetting('qrEnabled', True)
            for delay, kind in ((100,'tv'),(850,'shutter'),(2050,'vinyl')):
                QTimer.singleShot(delay, lambda k=kind: controller.transitionRequested.emit(k))
            QTimer.singleShot(3350, lambda: controller.transitionRequested.emit('flashcolor'))
            QTimer.singleShot(3500, controller.testDrop)
        # Exercise a second actual native window without network/capture.
        QTimer.singleShot(800, controller.openTranslation)
        if args.smoke_settings:
            def show_settings():
                output = Path(args.smoke_output).resolve()
                output.parent.mkdir(parents=True, exist_ok=True)
                first.grabWindow().save(str(output.with_stem(output.stem + "-screen")))
                panel = first.findChild(QObject, "settingsPanel")
                panel.setProperty("currentTab", args.smoke_tab)
                QMetaObject.invokeMethod(first, "openSettings")
            QTimer.singleShot(1800, show_settings)

        def capture():
            nonlocal result_code
            output = Path(args.smoke_output).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            saved = first.grabWindow().save(str(output))
            panel = first.findChild(QObject, "settingsPanel")
            report = {"api": first.rendererInterface().graphicsApi().name,
                      "frames": first.property("frames"), "seconds": round(time.monotonic()-started, 2),
                      "windows": len(windows), "font": family, "saved": saved, "warnings": warnings,
                      "settings_visible": bool(panel and panel.property("visible"))}
            if args.smoke_transition:
                report['swap_hidden_in_all_windows'] = transition_checks == [True]
                report['transition_finished'] = not controller.view['transitionPhase'] and controller.loaded_track == 'next-smoke'
            output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            if sys.stdout:
                print(json.dumps(report, ensure_ascii=False))
            result_code = 0 if saved and report["frames"] > 10 and not warnings and (not args.smoke_settings or report["settings_visible"]) else 1
            if args.smoke_transition and not (report['swap_hidden_in_all_windows'] and report['transition_finished']):
                result_code = 1
            app.quit()

        QTimer.singleShot(4000, capture)
    app.exec()
    # Explicitly destroy scenes while their controller/context is still alive.
    for engine in engines:
        delete(engine)
    qInstallMessageHandler(None)
    log.close()
    return result_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FIESTA-Native"
        data.mkdir(parents=True, exist_ok=True)
        (data / "startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        if sys.stderr:
            traceback.print_exc()
        if sys.platform == "win32" and "--smoke-test" not in sys.argv:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, "No se pudo iniciar FIESTA. Consulta " + str(data / "startup-error.log"), "FIESTA", 0x10)
        sys.exit(1)
