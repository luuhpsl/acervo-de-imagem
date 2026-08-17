# Instruções do projeto

## Leia primeiro

1. README.md
2. docs/architecture.md
3. docs/development-process.md
4. docs/testing.md
5. docs/building.md

## Processo obrigatório

1. Entenda a solicitação e os critérios de aceite.
2. Inspecione os arquivos relevantes e os testes existentes.
3. Apresente um plano para mudanças que afetam vários arquivos.
4. Mantenha as alterações dentro do escopo solicitado.
5. Adicione ou atualize testes para mudanças de comportamento.
6. Execute `python scripts/dev.py validate`.
7. Revise o diff final.
8. Atualize a documentação afetada.

## Arquitetura

- Organize as capacidades do produto em `src/<pacote>/features`.
- Não importe módulos internos de outra feature.
- Use a interface pública das features (o `__init__.py` de cada uma).
- Mantenha a lógica de negócio em `model.py` e a orquestração compartilhada em `use_cases.py`.
- Mantenha APIs externas e persistência atrás de serviços (`services.py`).
- Isole adaptações de interface: `commands.py` para CLI e `gui.py` para GUI.
- Mantenha as composições `src/<pacote>/cli.py` e `src/<pacote>/gui.py` sem regra de negócio.
- Mantenha `shared` neutro em relação ao domínio.
- Não adicione abstrações sem necessidade demonstrada.

## Escopo

- Não expanda o escopo além do solicitado.
- Uma funcionalidade por vez.

## Dependências

- Não adicione dependências sem explicar a necessidade.
- Prefira a biblioteca padrão (stdlib) e dependências já existentes.
- O template começa com zero dependências de runtime — mantenha assim quando possível.
- Nunca faça commit de segredos.

## Qualidade de código

- Todo código novo tem type hints e passa no mypy em modo estrito.
- Formatação e lint são feitos pelo Ruff (`python scripts/dev.py format` / `lint`).
- Funções e módulos públicos têm docstrings claras.
- Prefira `pathlib` a manipulação de strings de caminho.
- Escreva código portável entre Windows, macOS e Linux.
- Não bloqueie o loop de eventos da GUI com I/O ou processamento demorado.

## Persistência e APIs

- Acesso a disco, rede ou variáveis de ambiente fica em `services.py`.
- `model.py` permanece puro: sem I/O, fácil de testar.

## Testes

- Toda mudança de comportamento deve considerar testes (pytest).
- Teste o resultado observável, não os detalhes internos.
- Teste GUI com casos de uso, controladores ou janelas falsas; não dependa de display real na suíte padrão.
- O `validate` exige 80% de cobertura. Não coloque lógica em `build_window` nem em `create_*_panel`: elas ficam fora da medição por exigirem display.

## Erros e diagnóstico

- Na CLI, escreva erros em `stderr` e retorne código diferente de zero; não use o logger para falar com o usuário.
- Na GUI, use o logger: um executável em modo windowed não tem terminal.

## Documentação

- Toda decisão relevante atualiza a documentação ou gera um ADR.

## Conclusão

Uma tarefa só está concluída quando critérios de aceite, testes,
cobertura, lint, typecheck, build, documentação e o CI estiverem
satisfeitos.
