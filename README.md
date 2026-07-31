# Acervo Visual Inteligente

Aplicação desktop em Python para catalogar imagens locais, gerar metadados com IA,
identificar duplicatas, criar thumbnails e enviar arquivos para Firebase Storage e
Firestore.

## Principais recursos

- Interface gráfica retrô em Tkinter.
- Login via Firebase Auth.
- Geração de metadados com OpenAI Vision.
- Suporte a JPG, JPEG, PNG, SVG, EPS e AI.
- Conversão de arquivos vetoriais para JPG de leitura.
- Upload de originais e thumbnails para Firebase Storage.
- Registro de metadados no Firestore.
- Controle de pendências quando a IA falha.
- Checkpoint de fila a cada 10 arquivos para reduzir risco de perda de progresso.
- Exportação para Excel.
- Tema claro/escuro.

## Estrutura adaptada do template

```text
src/acervo_visual_inteligente/
├── gui.py              # entrada da interface desktop
├── catalogo_logic.py   # motor de processamento do acervo
├── auth_server.py      # servidor local de autenticação
├── LAYOUT/             # ícones e assets da interface
├── Font/               # fontes locais
├── acervo.ico
└── index.html          # vitrine/local preview
```

## Configuração

Copie `.env.example` para `.env.local` e preencha:

```env
OPENAI_API_KEY=
FIREBASE_API_KEY=
FIREBASE_PROJECT_ID=uniasselvi-digital
FIREBASE_STORAGE_BUCKET=uniasselvi-digital.appspot.com
```

> Não faça commit de `.env.local`, `token.json`, `credentials.json` ou outros
> arquivos de credenciais.

## Instalação

Com `uv`:

```bash
uv sync
```

Com `pip`:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Execução

Com o pacote instalado:

```bash
acervo-visual-gui
```

Ou diretamente:

```bash
python -m acervo_visual_inteligente
```

## Validação rápida

```bash
python -m py_compile src/acervo_visual_inteligente/gui.py src/acervo_visual_inteligente/catalogo_logic.py src/acervo_visual_inteligente/auth_server.py
pytest
```
