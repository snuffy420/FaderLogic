#ifndef AppVersion
#define AppVersion "1.4.0"
#endif
[Setup]
AppId={{6731735A-A91C-4DF6-A8AF-EF81A3A9A464}
AppName=FaderLogic
AppVersion={#AppVersion}
AppPublisher=zerØ software
AppPublisherURL=https://github.com/snuffy420
AppCopyright=Copyright (C) 2026 zerØ software
DefaultDirName={autopf}\FaderLogic
DefaultGroupName=FaderLogic
DisableProgramGroupPage=yes
SetupArchitecture=x64
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline
OutputDir=..\releases
OutputBaseFilename=FaderLogic-{#AppVersion}-windows-x64-setup
SetupIconFile=..\assets\faderlogic.ico
UninstallDisplayIcon={app}\FaderLogic.exe
UninstallDisplayName=FaderLogic {#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoCompany=zerØ software
VersionInfoDescription=FaderLogic {#AppVersion} x64 Setup
VersionInfoProductName=FaderLogic
LicenseFile=..\LICENSE
WizardStyle=modern dark includetitlebar
WizardBackColor=$1C1816
WizardImageBackColor=$1C1816
WizardImageFile=..\assets\installer-side.bmp
WizardSmallImageFile=..\assets\installer-small.bmp
WizardImageStretch=yes
WizardSizePercent=110,110
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
DisableWelcomePage=no
DisableDirPage=no
Uninstallable=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\build\installer-payload\FaderLogic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed.flag"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FaderLogic"; Filename: "{app}\FaderLogic.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall FaderLogic"; Filename: "{uninstallexe}"
Name: "{autodesktop}\FaderLogic"; Filename: "{app}\FaderLogic.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\FaderLogic.exe"; Description: "Launch FaderLogic"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Messages]
WelcomeLabel2=This will install FaderLogic {#AppVersion} on your computer.%n%nYour playlists and preferences are stored separately in your user profile. Uninstalling FaderLogic keeps that saved data.%n%nClick Next to continue.
