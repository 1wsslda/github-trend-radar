#define MyAppName "GitSonar"
#define MyAppExeName "GitSonar.exe"
#define MyAppVersion "1.0.0"

[Setup]
AppId={{B6C14561-0A25-4A2A-9C89-C2D6E9B3F6D0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=OpenAI Codex
DefaultDirName={autopf64}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\artifacts\dist\installer
OutputBaseFilename=GitSonarSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\artifacts\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
