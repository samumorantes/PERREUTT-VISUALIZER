"""One packaged smoke check; keep the renderer evidence with CI artifacts."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from native_platform import data_directory
executable = root / {'win32': 'dist/FIESTA/FIESTA.exe',
                     'darwin': 'dist/FIESTA.app/Contents/MacOS/FIESTA'}.get(sys.platform, 'dist/FIESTA/FIESTA')
output = root / 'build/smoke.png'
output.parent.mkdir(exist_ok=True)
command = [str(executable), '--smoke-test', '--smoke-output', str(output)]
if sys.platform == 'linux' and not os.environ.get('DISPLAY'):
    command = ['xvfb-run', '-a'] + command
try:
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    detail = 'Exit code: ' + str(result.returncode) + '\n' + result.stdout + result.stderr
    report_path = output.with_suffix('.json')
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    detail += '\n' + json.dumps(report, ensure_ascii=False, indent=2)
    failed = result.returncode or not report.get('saved') or report.get('frames', 0) <= 10 or report.get('warnings')
    error_log = data_directory() / 'startup-error.log'
    if failed and error_log.exists():
        detail += '\n' + error_log.read_text(encoding='utf-8')[-4000:]
except subprocess.TimeoutExpired as exc:
    detail, failed = str(exc), True
(root / 'build/render.log').write_text(detail, encoding='utf-8')
print(detail)
if failed:
    # Make remote failures diagnosable through public check annotations as well
    # as the downloadable logs; no account credentials are involved in smoke.
    message = detail[-2800:].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print('::error::' + message)
    raise SystemExit(1)
