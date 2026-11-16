#ifndef AppVersion
  #define AppVersion "2.6.0"
#endif

[Setup]
AppId={{C2BF6EB1-A762-4A10-9A76-4A956F5CFEBA}
AppName=FIESTA Native
AppVersion={#AppVersion}
AppVerName=FIESTA Native {#AppVersion}
AppPublisher=FIESTA
AppPublisherURL=https://github.com/samumorantes/PERREUTT-VISUALIZER
DefaultDirName={localappdata}\Programs\FIESTA-Native
DefaultGroupName=FIESTA Native
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\releases
OutputBaseFilename=FIESTA-Native-Setup-{#AppVersion}
SetupIconFile=..\fiesta.ico
UninstallDisplayIcon={app}\FIESTA.exe
WizardStyle=modern
WizardImageFile=wizard.png
WizardSmallImageFile=badge.png
InfoBeforeFile=welcome.txt
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
CloseApplicationsFilter=FIESTA.exe
RestartApplications=no
SetupLogging=yes
VersionInfoVersion={#AppVersion}.0
VersionInfoDescription=Instalador de FIESTA Native

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\FIESTA\FIESTA.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\FIESTA\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FIESTA Native"; Filename: "{app}\FIESTA.exe"; WorkingDir: "{app}"
Name: "{group}\Desinstalar FIESTA Native"; Filename: "{uninstallexe}"
Name: "{userdesktop}\FIESTA Native"; Filename: "{app}\FIESTA.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\FIESTA.exe"; Description: "Abrir FIESTA Native"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

; Settings/tokens live outside {app}, in LOCALAPPDATA\FIESTA-Native.
; Deliberately no UninstallDelete: uninstall must preserve personal data.
