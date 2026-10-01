#define MyAppName "Network Automation"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Network Automation"
#define MyAppExeName "NetworkAutomation.exe"

[Setup]
AppId={{9F91D742-449B-4E5D-B7E2-BDE376E83746}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\NetworkAutomation
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=NetworkAutomation_Setup_v1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
SetupLogging=yes

[Files]
Source: "..\dist\NetworkAutomation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài Desktop"; GroupDescription: "Biểu tượng bổ sung:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Mở {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Intentionally do NOT delete %LOCALAPPDATA%\NetworkAutomation.
; Database, credential key, reports and logs survive an application upgrade/uninstall.
Type: filesandordirs; Name: "{app}"
