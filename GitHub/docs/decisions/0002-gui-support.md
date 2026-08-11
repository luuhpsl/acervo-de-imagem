# 0002 - Suporte a aplicações CLI e GUI

- **Status**: Aceito
- **Data**: 2026-07-26

## Contexto

O template inicial tratava toda aplicação como CLI. Isso limitava produtos destinados a pessoas que precisam de uma janela desktop, embora regras de negócio, persistência e qualidade sejam iguais nas duas formas de interação.

Precisamos permitir CLI, GUI ou ambas sem duplicar lógica e sem obrigar projetos somente de terminal a carregar um toolkit gráfico.

## Decisão

- Manter `model.py` puro e `services.py` responsável por I/O.
- Adicionar `use_cases.py` em cada feature para compartilhar orquestração entre interfaces.
- Usar `commands.py` como adaptador CLI e `gui.py` como adaptador GUI da feature.
- Manter `src/<pacote>/cli.py` e `src/<pacote>/gui.py` como composições neutras.
- Preservar `python -m <pacote>` e o script existente como entradas CLI.
- Adicionar um `project.gui-scripts` para iniciar a GUI.
- Usar Tkinter no exemplo por pertencer à stdlib e não adicionar dependência Python de runtime.
- Carregar Tkinter somente ao criar a janela, preservando CLI e testes em ambientes headless.
- Permitir ao build PyInstaller selecionar `--interface cli` ou `--interface gui`; builds GUI usam modo windowed.
- Testar a entrada GUI com uma janela falsa, sem exigir display na suíte padrão.

## Alternativas consideradas

- **Somente documentar uma pasta GUI futura**: não comprova que setup, build, tipos e testes realmente suportam aplicações gráficas.
- **Framework externo por padrão**: oferece mais componentes, mas adiciona dependência e impõe uma escolha antes de existir necessidade concreta.
- **Duplicar a orquestração em CLI e GUI**: simplifica arquivos pequenos, mas cria comportamentos divergentes à medida que o produto cresce.
- **Abrir a GUI por padrão em `python -m`**: quebraria a compatibilidade e automações que já usam a CLI.

## Consequências

Positivas:

- Um mesmo produto pode oferecer terminal e janela sem duplicar regras.
- Projetos somente CLI não carregam Tkinter durante imports normais.
- O template demonstra build e teste headless das duas interfaces.
- Pessoas não desenvolvedoras podem receber um executável GUI sem console.

Limitações:

- Tkinter pode exigir um pacote do sistema em algumas distribuições Linux.
- A GUI de exemplo é intencionalmente simples; interfaces ricas podem justificar outro toolkit e um novo ADR.
- Trabalho demorado exige cuidado para não bloquear o loop de eventos.
- Executáveis continuam precisando ser gerados separadamente em cada sistema operacional.
