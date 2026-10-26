#ifndef AppVersion
#define AppVersion "1.4.0"
#endif
[Setup]
AppId={{31B8D0B6-96F3-4A49-8584-A6B20822D9BA}
AppName=MixLogic
AppVersion={#AppVersion}
AppPublisher=zerØ software
AppPublisherURL=https://github.com/snuffy420
AppCopyright=Copyright (C) 2026 zerØ software
DefaultDirName={autopf}\MixLogic
DefaultGroupName=MixLogic
DisableProgramGroupPage=yes
SetupArchitecture=x64
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline
OutputDir=..\releases
OutputBaseFilename=MixLogic-{#AppVersion}-windows-x64-setup
SetupIconFile=..\assets\mixlogic.ico
UninstallDisplayIcon={app}\MixLogic.exe
UninstallDisplayName=MixLogic {#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoCompany=zerØ software
VersionInfoDescription=MixLogic {#AppVersion} x64 Setup
VersionInfoProductName=MixLogic
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
Source: "..\build\installer-payload\MixLogic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed.flag"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MixLogic"; Filename: "{app}\MixLogic.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall MixLogic"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MixLogic"; Filename: "{app}\MixLogic.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\MixLogic.exe"; Description: "Launch MixLogic"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Messages]
WelcomeLabel2=This will install MixLogic {#AppVersion} on your computer.%n%nYour playlists and preferences are stored separately in your user profile. Uninstalling MixLogic keeps that saved data.%n%nClick Next to continue.
