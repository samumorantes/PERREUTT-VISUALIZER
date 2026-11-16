"""Build on the target OS. No cross-compilation or browser runtime."""
import argparse
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    import PySide6
    from PySide6.QtCore import QLibraryInfo
    from fontTools.ttLib import TTFont
    qt = Path(PySide6.__file__).parent
    candidates = [qt / 'qsb.exe', qt / 'Qt' / 'libexec' / 'qsb',
                  Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.LibraryExecutablesPath)) / 'qsb']
    qsb = next((p for p in candidates if p.is_file()), None)
    if qsb is None:
        raise RuntimeError('Qt shader baker not found in this Python environment')
    for source in sorted((ROOT / 'desktop/shaders').glob('*.frag')):
        subprocess.run([str(qsb), '--qt6', '-o', str(source.with_suffix('.qsb')), str(source)], check=True)
    for source, dest in [('arcadeclassic_full.woff', 'arcade.ttf'), ('spacegrotesk.woff2', 'grotesk.ttf')]:
        font = TTFont(ROOT / 'fonts' / source)
        font.flavor = None
        font.save(ROOT / 'desktop' / dest)
    # PNG-backed ICNS entries, generated from the existing application icon.
    if sys.platform == 'darwin':
        from PySide6.QtGui import QImage
        from PySide6.QtCore import QBuffer, QIODevice, Qt
        import struct
        source = QImage(str(ROOT / 'fiesta.ico'))
        if source.isNull():
            raise RuntimeError('Cannot read application icon')
        entries = []
        for tag, size in [(b'ic07',128), (b'ic08',256), (b'ic09',512)]:
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            source.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation).save(buffer, 'PNG')
            data = bytes(buffer.data())
            entries.append(tag + struct.pack('>I', len(data)+8) + data)
        data = b''.join(entries)
        (ROOT / 'desktop/fiesta.icns').write_bytes(b'icns' + struct.pack('>I', len(data)+8) + data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    os.chdir(ROOT)
    prepare()
    if not args.prepare_only:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', 'fiesta_desktop.spec'], check=True)
