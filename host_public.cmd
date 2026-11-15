@echo off
setlocal
cd /d "%~dp0"
title FIESTA - acceso desde el movil
if not exist "tools\cloudflared.exe" (
  echo Descargando cloudflared...
  powershell -NoProfile -Command "New-Item -ItemType Directory -Force tools | Out-Null; Invoke-WebRequest -UseBasicParsing 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'tools\cloudflared.exe'"
  if not exist "tools\cloudflared.exe" (
    echo No se pudo descargar cloudflared.
    pause
    exit /b 1
  )
)
echo.
echo Abriendo tunel publico hacia http://127.0.0.1:8888
echo Copia el enlace https://...trycloudflare.com que aparece abajo y abrelo en el movil.
echo Deja esta ventana abierta mientras lo uses: si la cierras, el enlace deja de funcionar.
echo.
"tools\cloudflared.exe" tunnel --url http://127.0.0.1:8888 --no-autoupdate
echo.
echo Tunel cerrado.
pause
