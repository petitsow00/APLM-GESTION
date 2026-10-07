; ====================================================================
;  Script Inno Setup - cree l'installateur APLM_Setup.exe
;  Le logiciel s'installe dans "Program Files", et ses donnees
;  (base, recus, logo) sont rangees dans Documents\APLM BUZNESS COMPANY.
; ====================================================================

#define MonApp "APLM BUZNESS COMPANY"
#define MaVersion "1.0"

[Setup]
AppName={#MonApp}
AppVersion={#MaVersion}
AppPublisher={#MonApp}
DefaultDirName={autopf}\APLM BUZNESS COMPANY
DisableProgramGroupPage=yes
OutputDir=C:\Users\Galileo\Downloads
OutputBaseFilename=APLM_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer une icone sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "C:\Users\Galileo\APLM_Voyages\dist\APLM\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "C:\Users\Galileo\APLM_Voyages\Autoriser le serveur (pare-feu).bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\APLM BUZNESS COMPANY"; Filename: "{app}\APLM.exe"
Name: "{autoprograms}\Autoriser le serveur (pare-feu)"; Filename: "{app}\Autoriser le serveur (pare-feu).bat"
Name: "{autodesktop}\APLM BUZNESS COMPANY"; Filename: "{app}\APLM.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\APLM.exe"; Description: "Lancer APLM BUZNESS COMPANY maintenant"; Flags: nowait postinstall skipifsilent
