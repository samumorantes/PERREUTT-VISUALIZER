"""One packaged smoke check; keep the renderer evidence with CI artifacts."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
executable = root / {'win32': 'dist/FIESTA/FIESTA.exe',
                     'darwin': 'dist/FIESTA.app/Contents/MacOS/FIESTA'}.get(sys.platform, 'dist/FIESTA/FIESTA')
output = root / 'build/smoke.png'
output.parent.mkdir(exist_ok=True)
subprocess.run([str(executable), '--smoke-test', '--smoke-output', str(output)], check=True, timeout=60)
report = json.loads(output.with_suffix('.json').read_text(encoding='utf-8'))
print(json.dumps(report, ensure_ascii=False, indent=2))
if not report['saved'] or report['frames'] <= 10 or report['warnings']:
    raise SystemExit('Packaged render check failed')
