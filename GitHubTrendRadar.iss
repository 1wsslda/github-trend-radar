#define MyAppName "GitHub Trend Radar"
#define MyAppExeName "GitHubTrendRadar.exe"
#define MyAppVersion "1.0.0"

[Setup]
AppId={{B6C14561-0A25-4A2A-9C89-C2D6E9B3F6D0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=OpenAI Codex
DefaultDirName={autopf64}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=dist\installer
OutputBaseFilename=GitHubTrendRadarSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
