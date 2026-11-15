# Run with Python 3.11+ available on PATH. Installs only into this app's venv.
$ErrorActionPreference = 'Stop'
$audioEnv = Join-Path $PSScriptRoot '.venv-audio'
python -m venv $audioEnv
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno de audio.' }
& (Join-Path $audioEnv 'Scripts\python.exe') -m pip install -r (Join-Path $PSScriptRoot 'requirements-audio.txt')
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias de audio.' }
Write-Host 'Audio instalado. Reinicia FIESTA para usarlo.'
