$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv-desktop/Scripts/python.exe')) {
    if (Test-Path '.venv-audio/Scripts/python.exe') {
        & '.venv-audio/Scripts/python.exe' -m venv .venv-desktop
    } else {
        python -m venv .venv-desktop
    }
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
}
& '.venv-desktop/Scripts/python.exe' -m pip install -r requirements-desktop.txt
if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación de dependencias.' }
Write-Host 'Entorno listo. Ejecuta .\build_desktop.ps1 para crear FIESTA.exe.'
