# Acervo de Imagens

Aplicação desktop em Python para catalogar acervos visuais locais com apoio de IA. O programa varre pastas do computador, identifica imagens e arquivos vetoriais, gera thumbnails, classifica o conteúdo com OpenAI Vision, envia os arquivos para Firebase Storage e registra os metadados no Firestore.

O objetivo do projeto é formar uma base organizada para um futuro banco de imagens, permitindo que pessoas pesquisem, visualizem thumbnails e baixem os arquivos originais em alta resolução.

## Recursos principais

- Interface gráfica desktop em Tkinter com tema retrô inspirado no Windows 98.
- Tema claro/escuro.
- Login via Firebase Authentication.
- Varredura recursiva de subpastas.
- Suporte a `.jpg`, `.jpeg`, `.png`, `.eps`, `.ai` e `.svg`.
- Conversão de arquivos vetoriais para JPG de leitura/thumbnail.
- Geração de metadados com OpenAI Vision (`gpt-4o-mini`).
- Criação de thumbnail para uso futuro no site.
- Upload de original e thumbnail para Firebase Storage.
- Registro de dados no Firestore.
- Detecção de duplicidade por hash SHA-256 e pHash.
- Preferência por variações coloridas quando existir versão colorida e preto-e-branco.
- Fila/checkpoint de processamento para reduzir perda de progresso.
- JSON de pendências para reprocessamento posterior.
- Botão para carregar JSON de retomada manualmente.
- Exportação para Excel.
- Vitrine HTML local para consulta simples.

## Estrutura principal

```text
.
├── README.md
├── AGENTS.md
├── pyproject.toml
├── storage.rules
├── Documentos/
│   └── Doc/
│       ├── arquitetura.md
│       ├── build-publicacao.md
│       ├── git-github-powershell.md
│       ├── uso.md
│       └── visao-geral.md
├── src/
│   └── acervo_visual_inteligente/
│       ├── __init__.py
│       ├── __main__.py
│       ├── auth_server.py
│       ├── catalogo_logic.py
│       ├── gui.py
│       ├── index.html
│       ├── acervo.ico
│       ├── Font/
│       └── Icons - Programa/
└── tests/
```

## Como instalar

Requisitos recomendados:

- Python 3.11 ou superior.
- Git para versionamento.
- ImageMagick e Ghostscript para converter EPS/AI/SVG quando necessário.
- Conta/projeto Firebase com Authentication, Firestore e Storage.
- Chave de API da OpenAI.

Instalação com `pip`:

```powershell
cd "C:\Users\lucas.silveira\Documents\Codex\2026-07-29\ol-chat-tenho-esse-programa-que\template-ia-python-master"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Instalação com `uv`, se disponível:

```powershell
uv sync
```

## Configuração

Copie `.env.example` para `.env.local` e preencha as chaves reais:

```powershell
Copy-Item .env.example .env.local
```

Variáveis esperadas:

```env
OPENAI_API_KEY=
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
FIREBASE_STORAGE_BUCKET=
FIREBASE_APP_ID=
```

Nunca faça commit de arquivos com credenciais, tokens ou chaves privadas.

## Como executar

Com o ambiente ativado:

```powershell
acervo-visual-gui
```

Ou:

```powershell
python -m acervo_visual_inteligente.gui
```

## Fluxo de uso

1. Abra o programa.
2. Faça login com uma conta autorizada.
3. Clique em `Selecionar Pasta`.
4. Aguarde a varredura.
5. Clique em `Play`.
6. Acompanhe o log, progresso, tempo e métricas laterais.
7. Se houver falhas, use `Reprocessar Pendentes`.
8. Se houver uma lista de retomada, use o botão de upload para carregar um JSON.

## Organização no Firebase

Cada ativo usa um único UUID no Firestore e no Storage:

```text
Firestore: acervo-visual-unificado/{uuid}

Storage: acervo-visual-unificado/{uuid}/
├── {uuid}_original.{extensao}
├── {uuid}_large.jpg
├── {uuid}_medium.jpg
└── {uuid}_thumb.jpg
```

Não são criadas subcoleções por origem ou ano. Descrição, cores, tipo visual e
palavras-chave ficam exclusivamente no documento do Firestore.

## Validação rápida

```powershell
python -m py_compile src\acervo_visual_inteligente\gui.py src\acervo_visual_inteligente\catalogo_logic.py src\acervo_visual_inteligente\auth_server.py
python -m pytest
```

Se `pytest` não estiver instalado:

```powershell
pip install -e ".[dev]"
```

## GitHub

Remote oficial:

[https://github.com/DevEdTech/Acervo-de-Imagens.git](https://github.com/DevEdTech/Acervo-de-Imagens.git)

Documentação de Git/PowerShell está em:

[Documentos/Doc/git-github-powershell.md](Documentos/Doc/git-github-powershell.md)

## Documentação complementar

- [Visão geral](Documentos/Doc/visao-geral.md)
- [Arquitetura](Documentos/Doc/arquitetura.md)
- [Uso](Documentos/Doc/uso.md)
- [Build e publicação](Documentos/Doc/build-publicacao.md)
- [Git, GitHub e PowerShell](Documentos/Doc/git-github-powershell.md)
