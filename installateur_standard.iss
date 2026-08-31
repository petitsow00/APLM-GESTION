; ====================================================================
;  Installateur de la VERSION STANDARD (personnalisable par chaque agence)
;  Produit : Gestion Agence de Voyages
;  Chaque agence saisit son nom/logo dans l'ecran "Reglages".
; ====================================================================

#define MonApp "Gestion Agence de Voyages"
#define MaVersion "1.0"

[Setup]
AppName={#MonApp}
AppVersion={#MaVersion}
AppPublisher={#MonApp}
DefaultDirName={autopf}\Gestion Agence de Voyages
DisableProgramGroupPage=yes
OutputDir=C:\Users\Galileo\Downloads
OutputBaseFilename=GestionVoyages_Setup
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
Source: "C:\Users\Galileo\APLM_Voyages\dist\GestionVoyages\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Gestion Agence de Voyages"; Filename: "{app}\GestionVoyages.exe"
Name: "{autodesktop}\Gestion Agence de Voyages"; Filename: "{app}\GestionVoyages.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GestionVoyages.exe"; Description: "Lancer le logiciel maintenant"; Flags: nowait postinstall skipifsilent
