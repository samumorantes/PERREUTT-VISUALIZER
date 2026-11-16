"""Platform policy, kept independent of Qt and audio drivers for testing."""
import os
from pathlib import Path
import sys


def data_directory(platform=None, env=None, home=None):
    platform = platform or sys.platform
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    if platform == "win32":
        return Path(env.get("LOCALAPPDATA", home)) / "FIESTA-Native"
    if platform == "darwin":
        return home / "Library" / "Application Support" / "FIESTA-Native"
    base = Path(env.get("XDG_DATA_HOME", home / ".local" / "share"))
    if not base.is_absolute():
        base = home / ".local" / "share"
    return base / "FIESTA-Native"


def graphics_backend(platform=None):
    return {"win32": "d3d11", "darwin": "metal"}.get(platform or sys.platform, "opengl")


def output_capture_device(soundcard, platform=None):
    """Select only an output monitor or BlackHole, never a default microphone."""
    platform = platform or sys.platform
    if platform == "linux":
        speaker = soundcard.default_speaker()
        monitor = str(speaker.id) + ".monitor"
        for device in soundcard.all_microphones(include_loopback=True):
            if str(device.id) == monitor and device.isloopback:
                return device
        raise RuntimeError("No hay monitor de salida. Activa PulseAudio o pipewire-pulse.")
    if platform == "darwin":
        for device in soundcard.all_microphones():
            if device.name == "BlackHole 2ch":
                return device
        raise RuntimeError("Instala BlackHole 2ch y configura una salida múltiple en Configuración de Audio MIDI.")
    raise RuntimeError("Plataforma de captura no compatible")
