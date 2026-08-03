# Build e publicação

Este documento descreve o caminho recomendado para preparar o programa para uso e publicação.

## Instalar dependências

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Validar código

Validação mínima:

```powershell
python -m py_compile src\acervo_visual_inteligente\gui.py src\acervo_visual_inteligente\catalogo_logic.py src\acervo_visual_inteligente\auth_server.py
```

Testes:

```powershell
python -m pytest
```

Se o ambiente ainda não tiver `pytest`, instale as dependências de desenvolvimento:

```powershell
pip install -e ".[dev]"
```

## Rodar localmente

```powershell
acervo-visual-gui
```

Ou:

```powershell
python -m acervo_visual_inteligente.gui
```

## Gerar executável

O projeto possui `pyinstaller` nas dependências de desenvolvimento. Um exemplo inicial:

```powershell
pyinstaller --noconsole --name "Acervo de Imagens" src\acervo_visual_inteligente\gui.py
```

Antes de empacotar oficialmente, conferir se os assets entram no build:

- `Icons - Programa/`
- `Font/`
- `acervo.ico`
- `index.html`
- arquivos necessários de autenticação/configuração

## Firebase

Antes de publicar para usuários:

1. Confirmar regras de Storage.
2. Confirmar regras de Firestore.
3. Confirmar usuários autorizados no Authentication.
4. Testar upload de thumbnail.
5. Testar upload de original raster.
6. Testar upload de original vector.
7. Testar gravação Firestore.

## OpenAI

Antes de processar acervo grande:

1. Confirmar chave ativa.
2. Rodar lote pequeno de teste.
3. Conferir custo no dashboard.
4. Garantir que o modelo segue usando `detail: low`.

## Checklist de publicação

- [ ] Versão atualizada.
- [ ] README atualizado.
- [ ] Documentação atualizada.
- [ ] `py_compile` passou.
- [ ] Testes passaram ou limitação foi informada.
- [ ] `.env.local` não está no commit.
- [ ] `token.json` não está no commit.
- [ ] Build local testado.
- [ ] Git status revisado.
