$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv-desktop/Scripts/python.exe'
if (-not (Test-Path $python)) { throw 'Ejecuta primero setup_desktop.ps1' }
& $python scripts/build_native.py
if ($LASTEXITCODE -ne 0) { throw 'Error al construir FIESTA Native.' }
Write-Host 'Listo: dist/FIESTA/FIESTA.exe. Conserva toda la carpeta FIESTA.'
