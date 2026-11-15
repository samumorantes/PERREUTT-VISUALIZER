# -*- coding: utf-8 -*-
"""FIESTA launcher — garantiza que el server esté vivo y abre la app en Edge/Chrome."""
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:8888/"
HEALTH = URL + "healthz"
LOG = os.path.join(HERE, "fiesta.log")

_log_file = None   # se mantiene abierto mientras viva el server: su salida va aquí


def server_alive():
    """Comprueba el latido /healthz (no gasta cuota de Spotify como /api/sync)."""
    try:
        with urllib.request.urlopen(HEALTH, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def start_server():
    """Arranca server.py con pythonw (sin consola) y deja su salida en fiesta.log."""
    global _log_file
    exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(exe):
        exe = sys.executable
    audio_exe = os.path.join(HERE, ".venv-audio", "Scripts", "pythonw.exe")
    if os.path.exists(audio_exe):
        exe = audio_exe
    _log_file = open(LOG, "ab", buffering=0)
    try:
        subprocess.Popen(
            [exe, os.path.join(HERE, "server.py")],
            cwd=HERE,
            stdin=subprocess.DEVNULL,
            stdout=_log_file,
            stderr=_log_file,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        _log_file.close()
        _log_file = None
        raise


def wait_server(seconds=8):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if server_alive():
            return True
        time.sleep(0.5)
    return False


def notify(msg):
    """Avisa al usuario sin consola (pythonw no tiene stdout visible)."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, msg, "FIESTA", 0x30)
    except Exception:
        print(msg)


def open_browser():
    """Edge en modo app (ventana propia); Chrome como respaldo."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for b in candidates:
        if os.path.exists(b):
            subprocess.Popen([b, "--start-maximized", "--app=" + URL])
            return
    import webbrowser
    webbrowser.open(URL)


def main():
    if not server_alive():
        try:
            start_server()
        except Exception as e:
            notify("No se pudo arrancar el servidor de FIESTA:\n\n%s" % e)
            return 1
        if not wait_server():
            notify("FIESTA no respondió a tiempo.\nRevisa el log: %s" % LOG)
            return 1
    open_browser()
    return 0


if __name__ == "__main__":
    sys.exit(main())
