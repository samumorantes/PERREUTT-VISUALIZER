param([switch]$SkipBuild, [string]$Compiler, [string]$Version = '2.5.0')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Versión no válida: usa X.Y.Z.' }
if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot 'build_desktop.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación nativa.' }
}
if (-not $Compiler) {
    $candidates = @((Join-Path $PSScriptRoot 'tools/inno/ISCC.exe'),
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")
    $Compiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $Compiler) {
        $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($command) { $Compiler = $command.Source }
    }
}
if (-not $Compiler -or -not (Test-Path -LiteralPath $Compiler)) {
    throw 'Instala Inno Setup 6 (jrsoftware.org) o pasa -Compiler con la ruta a ISCC.exe.'
}
$payload = Join-Path $PSScriptRoot 'dist/FIESTA'
if (-not (Test-Path -LiteralPath (Join-Path $payload 'FIESTA.exe'))) { throw 'Falta dist/FIESTA/FIESTA.exe.' }
$privateFiles = Get-ChildItem -LiteralPath $payload -File -Recurse |
    Where-Object { $_.Name -in @('token.json','spicy_key.txt','desktop-settings.json','.env','config.json') }
if ($privateFiles) { throw 'El paquete contiene archivos privados; no se generará el instalador.' }
& $Compiler "/DAppVersion=$Version" (Join-Path $PSScriptRoot 'installer/FIESTA.iss')
if ($LASTEXITCODE -ne 0) { throw 'Falló Inno Setup.' }
$artifact = Join-Path $PSScriptRoot "releases/FIESTA-Native-Setup-$Version.exe"
$digest = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
"$digest  $([IO.Path]::GetFileName($artifact))" | Set-Content -LiteralPath "$artifact.sha256" -Encoding ASCII
Write-Host "Instalador listo: $artifact"
