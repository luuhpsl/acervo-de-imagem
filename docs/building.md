# Build e distribuição

O projeto usa o template Python com `pyproject.toml`, `hatchling` e script de build com PyInstaller.

## Instalar para desenvolvimento

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

## Rodar a GUI

```bash
python -m acervo_visual_inteligente
```

ou, após instalação:

```bash
acervo-visual-gui
```

## Gerar executável GUI

```bash
python scripts/dev.py build-exe --interface gui --name acervo-visual-gui
```

O executável é gerado em `dist/`. O build deve ser feito no sistema operacional de destino.

## Variáveis necessárias

Configure localmente, sem versionar:

```env
OPENAI_API_KEY=
FIREBASE_API_KEY=
FIREBASE_PROJECT_ID=uniasselvi-digital
FIREBASE_STORAGE_BUCKET=uniasselvi-digital.appspot.com
```
