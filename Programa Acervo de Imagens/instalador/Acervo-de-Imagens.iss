#define MyAppName "Acervo de Imagens"
#define MyAppVersion "2.0.11"
#define MyAppPublisher "Produção Digital"
#define MyAppExeName "Acervo-de-Imagens.exe"
#define SourceDist "C:\\Users\\lucas.silveira\\Documents\\Codex\\2026-07-29\\ol-chat-tenho-esse-programa-que\\meu_catalogo_continuacao\\Programa Acervo de Imagens\\executavel\\nuitka313\\main.dist"
#define OutputPath "C:\\Users\\lucas.silveira\\Documents\\Codex\\2026-07-29\\ol-chat-tenho-esse-programa-que\\meu_catalogo_continuacao\\Programa Acervo de Imagens\\executavel"

[Setup]
AppId={{A3D0F4E6-8991-4E4C-8B6F-A1C3E7A20200}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=C:\Acervo-de-Imagens
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir={#OutputPath}
OutputBaseFilename=Instalador-Acervo-de-Imagens-v{#MyAppVersion}
SetupIconFile={#SourceDist}\Acervo.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce

[Files]
; Copia a pasta standalone inteira gerada pelo Nuitka.
; Nao leva token.json porque ele pertence ao login pessoal da maquina onde foi gerado.
Source: "{#SourceDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "token.json,__pycache__\*,*.pyc,*.pyo"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\Acervo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\Acervo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
