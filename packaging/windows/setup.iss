#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef ProjectRoot
  #error ProjectRoot is required
#endif

[Setup]
AppId={{E5A034AD-7737-4698-A1FD-E0E83DB8DFB4}
AppName=Piksel Atölyesi
AppVersion={#AppVersion}
AppPublisher=Teknoloji Filozofları
AppPublisherURL=https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game
AppSupportURL=https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/issues
DefaultDirName={localappdata}\Programs\Piksel Atolyesi
DefaultGroupName=Piksel Atölyesi
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#ProjectRoot}\dist
OutputBaseFilename=Piksel-Atolyesi-{#AppVersion}-Setup-x64
SetupIconFile={#ProjectRoot}\src\pixel_coloring\resources\icons\piksel-atolyesi.ico
UninstallDisplayIcon={app}\Piksel-Atolyesi.exe
LicenseFile={#ProjectRoot}\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "{#ProjectRoot}\build\windows\Piksel-Atolyesi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Piksel Atölyesi"; Filename: "{app}\Piksel-Atolyesi.exe"; AppUserModelID: "PixelColoring.PikselAtolyesi"
Name: "{autodesktop}\Piksel Atölyesi"; Filename: "{app}\Piksel-Atolyesi.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Piksel-Atolyesi.exe"; Description: "{cm:LaunchProgram,Piksel Atölyesi}"; Flags: nowait postinstall skipifsilent
