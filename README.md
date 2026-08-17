# python-project-template

Template de projeto Python para aplicações com linha de comando ou interface gráfica, pensado para pessoas que constroem ferramentas com a ajuda de agentes de código. Vem com organização de pastas, padrões de qualidade, testes, **build multiplataforma (Windows, macOS e Linux)** e instruções para agentes já prontos.

## Objetivo

Dar um ponto de partida seguro e organizado para criar aplicações Python simples, com CLI, GUI ou ambas. Você descreve o que quer, o agente implementa seguindo as regras deste template, e você valida com um único comando.

## Quando usar

Indicado para:

- Ferramentas de linha de comando (CLI)
- Aplicações desktop simples com interface gráfica (GUI)
- Automações e scripts de processamento
- Utilitários de dados (leitura/transformação de arquivos)
- Protótipos e provas de conceito
- Pequenos serviços sem interface web
- Bibliotecas simples reutilizáveis

## Quando NÃO usar (versão 1)

- Aplicações web com front-end (use o `project-template` de React)
- Sistemas de alta criticidade ou financeiros
- Serviços que exigem autenticação real e armazenamento seguro de segredos
- Pipelines de dados de grande escala ou infraestrutura crítica
- Aplicativos móveis ou interfaces gráficas ricas, 3D ou multimídia avançada

## Pré-requisitos

- Python 3.13 (a mesma versão em `.python-version`, no `requires-python` e no CI)
- [uv](https://docs.astral.sh/uv/) (recomendado) — ou `pip` + `venv` como alternativa
- git
- Um agente de código (ex.: Claude Code)

> **Por que uv?** É rápido, resolve dependências de forma determinística (`uv.lock`), gerencia o ambiente virtual e a versão do Python, e funciona igual nos três sistemas operacionais. Se preferir, tudo funciona com `pip` — veja a alternativa em cada passo.

## Criar um novo projeto a partir do template

1. Crie o repositório a partir deste template (botão "Use this template" no GitHub) ou copie a pasta.
2. Entre na pasta do projeto.
3. Instale as dependências e rode o setup:

```bash
uv sync                        # cria o .venv e instala tudo (runtime + dev)
python scripts/setup_project.py
```

Com `pip`, em vez de `uv sync`:

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e ".[dev]"
python scripts/setup_project.py
```

O `setup_project.py` separa nome exibido, distribuição, comando e pacote importável; personaliza descrição, organização, licença e repositório; mantém somente `--interface cli`, `gui` ou `both`; pode remover a demonstração sem quebrar a composição; e sincroniza as skills. Use `--dry-run` para revisar o plano. Repetições com os mesmos valores são idempotentes e falhas restauram o estado anterior.

## Prompts Iniciais (Copie, Preencha e Cole no Agente)

Escolha o cenário que se encaixa no seu momento e cole no seu agente de IA.

**Cenário A — "Tenho uma ideia mas não sei o escopo"** *(fluxo completo)*
```text
Estou começando um projeto novo. Faça o seguinte:
1. Rode `uv sync` e depois `python scripts/setup_project.py --name="[meu-app]" --display-name="[Meu App]" --description="[descreva aqui]" --remove-example --reset-tasks`.
2. Depois, use a skill plan-app para conduzir uma entrevista curta comigo e definirmos juntos o escopo do produto.
```

**Cenário B — "Já sei o que quero, planeje a feature"**
```text
O produto já está definido em docs/prd.md. Use a skill plan-feature para planejar a funcionalidade: [descreva a funcionalidade aqui]. Quero revisar o plano antes da implementação.
```

**Cenário C — "O plano foi aprovado, implemente"**
```text
O plano foi aprovado. Use a skill implement-feature para executar. Garanta que `python scripts/dev.py validate` passe limpo ao concluir.
```

## Execução

Rode a CLI de exemplo:

```bash
uv run app-template --help
uv run app-template notes add "Minha nota"
uv run app-template notes list
```

Abra a GUI de exemplo:

```bash
uv run app-template-gui
# ou
uv run python -m app_template.gui
```

Sem uv, ative o ambiente e use `app-template`, `app-template-gui` ou `python -m app_template`.

## Validação

Antes de considerar qualquer alteração pronta, rode:

```bash
python scripts/dev.py validate
```

Esse comando executa, em sequência: sincronização e verificação das skills, arquitetura e documentação, formatação, lint, checagem de tipos, testes com cobertura mínima, build e instalação do wheel em um ambiente limpo. Se todos passarem, a alteração está saudável.

O `validate` funciona sem rede e vale para um clone recém-feito.

### Verificação automática

O GitHub Actions repete o `validate` a cada push e Pull Request, em **Python 3.13**, no **Linux e no Windows** — os dois sistemas em que o template promete comportamento idêntico. Um workflow separado audita as dependências (`pip-audit` sobre o `uv.lock`) e varre o histórico em busca de segredos (`gitleaks`), também uma vez por semana para que uma vulnerabilidade nova apareça sem depender de um push.

Localmente, instale os hooks para receber o mesmo retorno antes do commit:

```bash
uv run pre-commit install
```

A auditoria depende de rede e por isso fica fora do `validate`; rode-a sob demanda:

```bash
python scripts/dev.py audit
```

O Dependabot verifica semanalmente as dependências do `uv` e as GitHub Actions,
abrindo pull requests para revisão sem fazer merge automático. Consulte
[SECURITY.md](SECURITY.md) para reportar vulnerabilidades de forma privada.

## Comandos

O runner `scripts/dev.py` é o equivalente cross-platform ao `npm run` — funciona igual no Windows, macOS e Linux.

| Comando                                  | O que faz                                                         |
| ---------------------------------------- | ---------------------------------------------------------------- |
| `python scripts/dev.py format`           | Formata o código com Ruff                                        |
| `python scripts/dev.py format-check`     | Confere a formatação sem alterar arquivos                        |
| `python scripts/dev.py lint`             | Verifica problemas de código com Ruff                            |
| `python scripts/dev.py lint-fix`         | Corrige automaticamente o que o Ruff conseguir                   |
| `python scripts/dev.py typecheck`        | Verifica os tipos com mypy (modo estrito)                        |
| `python scripts/dev.py test`             | Roda os testes com pytest                                        |
| `python scripts/dev.py test-cov`         | Roda os testes medindo cobertura                                 |
| `python scripts/dev.py build`            | Gera o pacote distribuível (wheel + sdist)                       |
| `python scripts/dev.py build-exe`        | Gera executável CLI ou GUI do SO atual (PyInstaller)             |
| `python scripts/dev.py sync-skills`      | Sincroniza as skills para `.claude/skills` e `.agents/skills`    |
| `python scripts/dev.py check-skills`     | Verifica se as cópias das skills estão sincronizadas             |
| `python scripts/dev.py check-architecture` | Verifica as fronteiras entre app, features e shared            |
| `python scripts/dev.py check-docs`       | Valida links, tarefas e referências da documentação              |
| `python scripts/dev.py generate-feature --name clientes` | Gera a estrutura inicial de uma feature           |
| `python scripts/dev.py smoke-package`    | Instala e testa o wheel em um ambiente limpo                     |
| `python scripts/dev.py check-workflows`  | Valida os workflows do GitHub Actions (actionlint)               |
| `python scripts/dev.py audit`            | Audita as dependências em busca de vulnerabilidades              |
| `python scripts/dev.py validate`         | Roda qualidade, testes, build e smoke do wheel                   |

> **Atalho Unix (opcional):** no macOS e Linux há um `Makefile` — `make validate`, `make test`, etc. No Windows, use os comandos `python scripts/dev.py <tarefa>` acima, que funcionam em qualquer sistema.

## Build para diferentes ambientes (Windows, macOS, Linux)

Há dois formatos de entrega, e o guia completo está em [docs/building.md](docs/building.md):

- **Pacote Python (wheel + sdist)** — multiplataforma por natureza. `python scripts/dev.py build` gera artefatos em `dist/` que instalam em qualquer SO com Python.
- **Executável standalone (PyInstaller)** — um binário que roda sem Python instalado. Use `python scripts/dev.py build-exe` para CLI ou acrescente `--interface gui` para GUI. O executável é gerado **para o sistema atual**; não há cross-compilação.

## Estrutura resumida

```
src/
└── app_template/         # pacote da aplicação (renomeado no setup)
    ├── __main__.py       # mantém `python -m app_template` como entrada CLI
    ├── cli.py            # composição da CLI — sem regra de negócio
    ├── gui.py            # composição da GUI — sem regra de negócio
    ├── features/         # cada capacidade do produto em sua pasta
    │   └── notes/        # demonstração canônica; removida por --remove-example
    │       ├── model.py      # lógica pura
    │       ├── services.py   # I/O e persistência
    │       ├── use_cases.py  # orquestração compartilhada
    │       ├── commands.py   # adaptador da CLI
    │       └── gui.py        # adaptador da GUI
    └── shared/           # reutilizável e neutro (types, lib)
tests/                    # espelham a estrutura das features
docs/                     # esta documentação
scripts/                  # runner e utilitários cross-platform
```

Detalhes em [docs/architecture.md](docs/architecture.md).

## Como usar agentes

As regras que os agentes devem seguir ficam em dois arquivos na raiz:

- `AGENTS.md` — regras gerais válidas para qualquer agente
- `CLAUDE.md` — instruções específicas para o Claude Code

Além disso, há skills que guiam tarefas comuns. Veja [docs/agents.md](docs/agents.md).

## Como criar uma feature

Se a ideia do aplicativo ainda não tem escopo fechado, comece com: "Use a skill plan-app para me ajudar a definir este produto". A skill conduz a conversa em linguagem simples, cria `docs/prd.md` após sua aprovação e registra as decisões em `docs/architecture.md`.

Depois que o produto estiver definido:

1. Peça ao agente um plano: "Use a skill plan-feature para planejar...".
2. Revise o plano.
3. Peça a implementação: "Use a skill implement-feature...".
4. Gere a base com `python scripts/dev.py generate-feature --name clientes`; acrescente `--interface cli`, `gui` ou `both` e `--dry-run` quando necessário. O gerador cria modelo, contrato de serviço, caso de uso, adaptadores compatíveis e teste, mas não registra a feature na composição.
5. Complete os testes observáveis da feature.
6. Rode `python scripts/dev.py validate`.

Regras de arquitetura em [docs/architecture.md](docs/architecture.md).

## Como registrar uma decisão

Decisões relevantes de arquitetura ou tecnologia viram um ADR (Architecture Decision Record) em `docs/decisions/`. Use o formato do primeiro registro, [0001-initial-architecture.md](docs/decisions/0001-initial-architecture.md), como modelo.

## Limitações conhecidas

- Zero dependências de runtime por padrão: a demonstração de notas usa só a biblioteca padrão.
- A GUI usa Tkinter, que pode exigir a instalação do pacote Tk do sistema em algumas distribuições Linux.
- Sem autenticação real nem armazenamento seguro de segredos.
- Executáveis nativos precisam ser gerados no próprio SO de destino (um build por sistema).
- Voltado a aplicações simples; não substitui projetos de alta criticidade.
