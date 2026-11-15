# Per-user native install. No administrator rights or background web server.
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'dist/FIESTA'
if (-not (Test-Path (Join-Path $source 'FIESTA.exe'))) {
    throw 'Primero ejecuta setup_desktop.ps1 y build_desktop.ps1.'
}
$destination = Join-Path $env:LOCALAPPDATA 'Programs/FIESTA-Native'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -LiteralPath (Join-Path $source 'FIESTA.exe') -Destination $destination -Force
Copy-Item -LiteralPath (Join-Path $source '_internal') -Destination $destination -Recurse -Force
$data = Join-Path $env:LOCALAPPDATA 'FIESTA-Native'
New-Item -ItemType Directory -Force -Path $data | Out-Null
foreach ($name in @('config.json', 'token.json', 'spicy_key.txt')) {
    $existing = Join-Path $PSScriptRoot $name
    if (-not (Test-Path -LiteralPath (Join-Path $data '.credentials-imported')) -and (Test-Path -LiteralPath $existing) -and -not (Test-Path -LiteralPath (Join-Path $data $name))) {
        Copy-Item -LiteralPath $existing -Destination $data
    }
}
New-Item -ItemType File -Path (Join-Path $data '.credentials-imported') -Force | Out-Null
$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$programs = [Environment]::GetFolderPath('Programs')
foreach ($folder in @($desktop, $programs)) {
    $shortcut = $ws.CreateShortcut((Join-Path $folder 'FIESTA Native.lnk'))
    $shortcut.TargetPath = Join-Path $destination 'FIESTA.exe'
    $shortcut.WorkingDirectory = $destination
    $shortcut.IconLocation = (Join-Path $destination 'FIESTA.exe') + ',0'
    $shortcut.Description = 'FIESTA nativo - GPU sin navegador'
    $shortcut.Save()
}
Write-Host "Instalado en $destination. Abre FIESTA Native desde el escritorio."
