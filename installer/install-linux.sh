#!/bin/sh
# Register this extracted folder in the user's applications menu. No root.
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
data_dir=${XDG_DATA_HOME:-"$HOME/.local/share"}
case "$data_dir" in /*) ;; *) data_dir="$HOME/.local/share" ;; esac
mkdir -p "$data_dir/applications" "$data_dir/icons/hicolor/256x256/apps"
cp "$app_dir/fiesta.png" "$data_dir/icons/hicolor/256x256/apps/fiesta-native.png"
# Escape Desktop Entry quoted Exec syntax, including percent field codes.
exec_path=$(printf '%s' "$app_dir/FIESTA" | sed 's/\\/\\\\/g; s/"/\\"/g; s/`/\\`/g; s/\$/\\$/g; s/%/%%/g')
cat > "$data_dir/applications/fiesta-native.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FIESTA Native
Comment=PERRE’UTT · Letras y percusión en una TV CRT
Exec="$exec_path"
Icon=fiesta-native
Terminal=false
Categories=AudioVideo;Music;
StartupWMClass=FIESTA Native
EOF
printf '%s\n' 'FIESTA está en el menú de aplicaciones. Conserva esta carpeta; el acceso directo la utiliza.'
