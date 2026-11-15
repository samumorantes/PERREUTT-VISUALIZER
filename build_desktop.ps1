$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv-desktop/Scripts/python.exe'
if (-not (Test-Path $python)) { throw 'Ejecuta primero .\setup_desktop.ps1' }
$qsb = Join-Path $PSScriptRoot '.venv-desktop/Lib/site-packages/PySide6/qsb.exe'
foreach ($name in @('background', 'crt', 'glass', 'lettering', 'transition')) {
    & $qsb --qt6 -o "desktop/shaders/$name.qsb" "desktop/shaders/$name.frag"
    if ($LASTEXITCODE -ne 0) { throw "No se pudo compilar $name" }
}
& $python -c "from fontTools.ttLib import TTFont; f=TTFont('fonts/arcadeclassic_full.woff'); f.flavor=None; f.save('desktop/arcade.ttf')"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar la fuente nativa.' }
& $python -c "from fontTools.ttLib import TTFont; f=TTFont('fonts/spacegrotesk.woff2'); f.flavor=None; f.save('desktop/grotesk.ttf')"
if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar Space Grotesk.' }
& $python -m PyInstaller --noconfirm fiesta_desktop.spec
if ($LASTEXITCODE -ne 0) { throw 'Falló el empaquetado.' }
Write-Host 'Listo: dist/FIESTA/FIESTA.exe. Conserva toda la carpeta FIESTA.'
