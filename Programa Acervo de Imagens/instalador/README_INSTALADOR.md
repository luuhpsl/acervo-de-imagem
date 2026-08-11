# Instalador - Acervo de Imagens

Este instalador usa Inno Setup e instala o programa em:

C:\Acervo-de-Imagens

## Importante

- O instalador inclui a pasta standalone do Nuitka inteira.
- O instalador NAO inclui token.json, porque esse arquivo e o login pessoal da maquina onde o build foi feito.
- O arquivo .env.local e incluido porque contem as configuracoes necessarias para Firebase/OpenAI.

## Como instalar o Inno Setup pelo PowerShell/CMD

winget install --id JRSoftware.InnoSetup -e

Depois feche e abra o PowerShell/CMD novamente.

## Como gerar o instalador

Entre na pasta do programa:

cd "C:\Users\lucas.silveira\Documents\Codex\2026-07-29\ol-chat-tenho-esse-programa-que\meu_catalogo_continuacao\Programa Acervo de Imagens"

Execute:

.\instalador\gerar_instalador.bat

O resultado sera criado em:

executavel\Instalador-Acervo-de-Imagens-v2.0.0.exe
