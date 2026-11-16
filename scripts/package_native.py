"""Create portable Linux archive or macOS disk image from a local native build."""
import hashlib
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '2.6.0'


def main():
    output = ROOT / 'dist/packages'
    output.mkdir(exist_ok=True)
    system = sys.platform
    if system == 'darwin':
        source = ROOT / 'dist/FIESTA.app'
    elif system == 'linux':
        source = ROOT / 'dist/FIESTA'
    else:
        raise RuntimeError('Use build_installer.ps1 on Windows')
    if not source.is_dir():
        raise RuntimeError('Build the application first')
    forbidden = {'config.json', 'token.json', 'spicy_key.txt', 'desktop-settings.json', '.env'}
    if any(p.name in forbidden for p in source.rglob('*')):
        raise RuntimeError('Private data in build payload; refusing to package')
    name = f'FIESTA-Native-{VERSION}-{system}-{platform.machine()}'
    if system == 'darwin':
        import tempfile
        artifact = output / (name + '.dmg')
        with tempfile.TemporaryDirectory(prefix='fiesta-dmg-') as tmp:
            staging = Path(tmp)
            shutil.copytree(source, staging / source.name, symlinks=True)
            (staging / 'Applications').symlink_to('/Applications')
            subprocess.run(['hdiutil', 'create', '-volname', 'FIESTA Native', '-srcfolder',
                            str(staging), '-ov', '-format', 'UDZO', str(artifact)], check=True)
    else:
        shutil.copy2(ROOT / 'installer/install-linux.sh', source / 'install-linux.sh')
        (source / 'install-linux.sh').chmod(0o755)
        from PySide6.QtGui import QImage
        if not QImage(str(ROOT / 'fiesta.ico')).save(str(source / 'fiesta.png')):
            raise RuntimeError('Cannot export Linux icon')
        artifact = output / (name + '.tar.gz')
        with tarfile.open(artifact, 'w:gz') as archive:
            archive.add(source, arcname='FIESTA')
    artifact.with_suffix(artifact.suffix + '.sha256').write_text(
        hashlib.sha256(artifact.read_bytes()).hexdigest() + '  ' + artifact.name + '\n')
    print(artifact)


if __name__ == '__main__':
    main()
