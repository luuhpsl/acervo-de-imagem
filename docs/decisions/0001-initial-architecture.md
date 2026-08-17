# 0001 - Arquitetura inicial

- **Status**: Aceito
- **Data**: 2026-07-24

## Contexto

Precisamos de um template Python que pessoas possam usar com agentes de código para criar aplicações simples (ferramentas de linha de comando, automações, utilitários de dados). O template deve ser fácil de entender, rápido de rodar, ter regras claras para que os agentes produzam código consistente e permitir **build para Windows, macOS e Linux**.

## Decisão

- **Stack**: Python 3.11+, `pyproject.toml` (PEP 621) com backend `hatchling` e **layout `src/`**.
- **Gerenciador**: `uv` como padrão (rápido, lockfile determinístico, gerencia venv e versão do Python), com `pip` + `venv` como alternativa documentada.
- **Qualidade embutida**: **Ruff** (lint + formatação, substituindo black/isort/flake8), **mypy** em modo estrito, **pytest** para testes, **pre-commit** opcional.
- **Zero dependências de runtime por padrão**: a feature de exemplo usa apenas a stdlib (`argparse`, `pathlib`, `json`).
- **Organização por features**: cada capacidade em sua pasta, com camadas `model` (puro), `services` (I/O) e `commands` (CLI). Base neutra em `cli.py` e `shared`.
- **Aplicação de exemplo = CLI**: uma CLI é naturalmente portável e pode ser empacotada tanto como wheel quanto como executável standalone.
- **Build multiplataforma**: wheel/sdist (multiplataforma por natureza) + PyInstaller (um executável por SO, gerado localmente em cada sistema).
- **Validação local única**: `python scripts/dev.py validate` roda check de skills, formatação, lint, typecheck, testes e build.
- **Runner cross-platform em Python puro**: `scripts/dev.py` substitui um Makefile (que não é nativo no Windows).

## Alternativas consideradas

- **Poetry**: maduro, mas mais lento que o uv e com resolução de ambiente própria; uv cobre os mesmos casos com melhor desempenho.
- **Layout "flat" (pacote na raiz)**: mais simples, mas propenso a importar o código local por engano nos testes; o layout `src/` é o padrão recomendado e evita essa classe de erro.
- **black + isort + flake8 separados**: mais peças para configurar; o Ruff faz tudo em uma ferramenta muito mais rápida.
- **Typer/Click para a CLI**: melhor ergonomia, mas adicionam dependência de runtime; `argparse` (stdlib) mantém o template com zero dependências. Migrar é um ADR futuro se a necessidade surgir.
- **Makefile como runner**: não é nativo no Windows; um script Python é verdadeiramente portável.
- **Testes colocalizados em `src/` (como no template web de React)**: em Python, o layout `src/` + `tests/` separado é o padrão e mantém o pacote distribuído limpo. Divergimos do template web de propósito, respeitando a idiomática da linguagem.

## Consequências

Positivas:

- Projeto rápido de iniciar e de rodar, com qualidade (tipos, lint, testes) embutida.
- Estrutura previsível, fácil de explicar a agentes e iniciantes.
- Cada feature é autocontida, o que reduz acoplamento.
- Uma única porta de validação (`dev.py validate`) simplifica o "está pronto?".
- Build para os três sistemas operacionais resolvido desde o início.

Limitações:

- Sem autenticação real, armazenamento seguro de segredos ou serviço web.
- Executáveis nativos precisam ser gerados no próprio SO de destino (um build por sistema).
- Escolhas mais avançadas (framework de CLI, cliente HTTP, carregador de `.env`) exigirão novos ADRs quando a necessidade surgir.
