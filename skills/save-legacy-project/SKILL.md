---
name: save-legacy-project
description: Diagnostica um projeto legado sem documentação nem organização e produz um plano aprovado de reestruturação em features, com documentação completa e validação, sem mudar o comportamento; use ao herdar, organizar ou padronizar um projeto que já existe.
---

# Salvar projeto legado

## Objetivo

Trazer ordem para um projeto desorganizado sem alterar o que ele faz.
A reestruturação é uma sequência de incrementos verificáveis: cada um
mantém o projeto funcionando, e o comportamento observável ao final é
idêntico ao do início.

O resultado é um projeto nos padrões da área: capacidades organizadas em
`src/<pacote>/features`, regra de negócio pura separada de I/O e de
interface, base neutra em `shared`, documentação completa em `docs/` e um
fluxo de desenvolvimento registrado.

## Regras

1. Preservar o comportamento observável. Reestruturação não é reescrita:
   mover, renomear e extrair; não redesenhar regras de negócio.
2. Separar mudança estrutural de mudança de comportamento. Se um bug
   aparecer no caminho, registrar e propor em separado, nunca corrigir
   junto com a movimentação de arquivos.
3. Não implementar nada antes da aprovação explícita do plano.
4. Um incremento por vez, cada um com commit próprio e reversível.
5. Não adicionar dependências. Preferir a biblioteca padrão e as
   dependências já presentes; qualquer exceção precisa de justificativa
   aprovada e ADR.
6. Não expandir o escopo: nada de features novas, troca de toolkit
   gráfico, redesenho de interface ou mudança de framework durante o
   resgate.
7. Nunca versionar segredos. Credenciais encontradas no código viram
   variáveis de ambiente lidas em `services.py` e um alerta explícito ao
   usuário.
8. Respeitar o histórico: usar `git mv` para mover arquivos e trabalhar
   em uma branch dedicada.
9. Adaptar o padrão ao projeto existente. As regras arquiteturais valem
   sempre; nomes de pacote, ferramental e comandos se ajustam ao que já
   existe, sem trocar de tecnologia.
10. Manter o código portável entre Windows, macOS e Linux e preferir
    `pathlib` a manipulação de strings de caminho.

## Fase 1 — Analisar

Antes de propor qualquer mudança, entender o que existe. Não perguntar
ao usuário o que o repositório pode responder.

Levantar:

- **Stack e execução**: versão de Python, gerenciador de ambiente e
  dependências (`uv`, `pip`, `poetry`, `requirements.txt`,
  `pyproject.toml`, `setup.py`), como se instala, roda, testa e empacota
  o projeto.
- **Pontos de entrada**: scripts soltos, `__main__.py`, `console_scripts`,
  subcomandos, janelas de GUI, jobs agendados ou notebooks.
- **Estrutura atual**: árvore de pastas, scripts na raiz, ausência de
  `src/`, pacote sem `__init__.py`, módulos gigantes e arquivos com
  muitas responsabilidades.
- **Capacidades do produto**: o que o sistema faz de fato, inferido dos
  comandos, telas, modelos de dados e nomes de módulo.
- **Fronteiras**: acesso a disco, rede, banco de dados, subprocessos,
  variáveis de ambiente e integrações externas.
- **Mistura de camadas**: regra de negócio dentro de código de interface,
  I/O no meio do cálculo, `print` e `input` usados como interface dentro
  da lógica, estado global em variáveis de módulo.
- **Acoplamentos**: importações cíclicas, imports com efeito colateral no
  carregamento do módulo, dependência entre partes que deveriam ser
  independentes.
- **Rede de segurança**: testes existentes, o que cobrem, se passam hoje,
  lint, checagem de tipos, cobertura de type hints, CI.
- **Riscos**: código morto, duplicação, segredos versionados,
  dependências abandonadas ou vulneráveis, comportamento não coberto por
  teste, uso de APIs removidas na versão de Python em uso.
- **Documentação**: o que existe, o que está desatualizado, o que falta.

Registrar o estado atual como fato verificado. Onde a leitura do código
não permitir concluir, marcar como dúvida a confirmar com o usuário, em
vez de supor.

Executar os comandos existentes de instalação, teste, lint e empacotamento
para saber o ponto de partida real. Se algo já falha antes da
reestruturação, registrar a falha como linha de base — não confundir com
regressão introduzida depois.

Ao final, apresentar um diagnóstico curto: o que o projeto faz, como está
organizado, quais são os cinco maiores problemas e qual é a rede de
segurança disponível.

## Fase 2 — Planejar

Produzir `docs/tasks/reestruturacao.md` usando
[assets/restructuring-plan-template.md](assets/restructuring-plan-template.md)
como estrutura mínima.

O plano precisa conter:

1. **Mapa de capacidades para features**: cada capacidade do produto vira
   uma pasta em `src/<pacote>/features`, com nome no domínio do negócio,
   não na camada técnica.
2. **Destino de cada arquivo atual**: tabela de origem para destino
   (`model.py`, `services.py`, `use_cases.py`, `commands.py`,
   `features/<nome>/gui.py`, composição em `cli.py` ou `gui.py` do
   pacote, `shared`, `tests/`, ou remoção justificada). Nenhum arquivo
   fica sem destino.
3. **Separação de camadas por arquivo**: o que de cada módulo atual é
   regra pura, o que é I/O e o que é apresentação, já indicando para qual
   arquivo cada parte vai.
4. **Interface pública de cada feature**: o que o `__init__.py` exporta e
   quais importações cruzadas precisam ser cortadas.
5. **Ordem dos incrementos**: começar pelo que dá rede de segurança e
   pelo que tem menos dependências. Ordem recomendada: rede de segurança
   e comandos de verificação, layout do pacote (`src/`), `shared`,
   features das mais isoladas para as mais acopladas, extração de
   `model.py` puro, isolamento de I/O em `services.py`, adaptação das
   interfaces, remoção do código morto, documentação.
6. **Type hints e mypy**: por onde a tipagem entra e em que ponto o modo
   estrito passa a valer, evitando um incremento único e gigante.
7. **Riscos e reversão**: o que pode quebrar em cada incremento e como
   voltar atrás.
8. **Não escopo**: features novas, mudança de framework ou de toolkit,
   redesenho de interface, correções de bug e otimizações — listadas
   explicitamente como fora do resgate, com encaminhamento separado.
9. **Critérios de aceite**: observáveis, incluindo a ausência de mudança
   de comportamento e o conjunto de verificações que passa ao final.

Apresentar ao usuário um resumo com `Diagnóstico`, `Mapa de features`,
`Incrementos`, `Riscos`, `Não escopo` e `Critérios de aceite`. Pedir
aprovação explícita. Se houver correção, revisar o plano; sem aprovação,
não seguir para a implementação.

## Fase 3 — Implementar

Aplicar um incremento por vez, na ordem aprovada.

Antes de mover um arquivo cujo comportamento não esteja coberto, escrever
um teste de caracterização: um teste que registra o comportamento atual
como ele é hoje, servindo de rede de segurança para a movimentação. Sem
esse teste, mover o código é aposta.

Para cada incremento:

1. Confirmar a rede de segurança do que será tocado.
2. Mover os arquivos com `git mv`, preservando o histórico.
3. Ajustar os imports e declarar a interface pública no `__init__.py` da
   feature.
4. Separar as camadas: regra pura em `model.py`, disco, rede, ambiente e
   subprocessos em `services.py`, orquestração em `use_cases.py`, CLI em
   `commands.py` e GUI em `features/<nome>/gui.py`.
5. Manter `cli.py` e `gui.py` do pacote apenas como composição, sem regra
   de negócio.
6. Adicionar type hints ao que foi tocado e executar as verificações do
   projeto, comparando com a linha de base.
7. Fazer um commit descritivo do incremento.

Não misturar incrementos no mesmo commit. Se um incremento crescer além
do previsto, parar, relatar e replanejar antes de continuar.

Manter o `docs/tasks/reestruturacao.md` atualizado, marcando o que já foi
concluído.

## Fase 4 — Documentar

Escrever a documentação que o projeto não tem, sempre a partir do código
verificado — nunca de suposição.

Criar ou atualizar:

- **`docs/prd.md`**: reconstruído a partir do comportamento existente —
  problema, usuários, jornada principal, capacidades atuais, interfaces
  (CLI, GUI ou ambas), regras de negócio, dados, integrações e critérios
  de aceite. Marcar claramente o que foi inferido do código e precisa de
  confirmação do usuário. Não inventar objetivos de produto.
- **`docs/architecture.md`**: layout final do pacote, responsabilidade de
  cada arquivo da feature, regras de dependência, fronteiras de I/O,
  interfaces oferecidas, empacotamento e trade-offs assumidos.
- **`docs/development-process.md`**: o fluxo desta área — analisar,
  planejar, implementar, documentar, testar, validar — com padrão de
  branch, mensagem de commit e definição de concluído.
- **`docs/testing.md`**: filosofia, tipos de teste, organização de
  `tests/` espelhando as features e comandos de execução.
- **`docs/building.md`**: versão de Python, criação do ambiente,
  instalação das dependências, execução, empacotamento e distribuição.
- **`docs/updating.md`**: como atualizar dependências, versão de Python e
  ferramental, e o que verificar depois.
- **`docs/integrations.md`**: integrações externas, variáveis de
  ambiente, comportamento em falha.
- **`docs/decisions/`**: um ADR numerado para cada decisão relevante do
  resgate, incluindo a própria adoção da organização por features e
  qualquer conflito resolvido com o usuário.
- **`docs/tasks/README.md`**: o modelo de tarefa usado pela área.
- **`AGENTS.md`** e **`CLAUDE.md`** na raiz: regras persistentes para
  agentes, coerentes com a arquitetura registrada.
- **`README.md`**: o que é o projeto, como instalar e rodar, tabela de
  tarefas de desenvolvimento e links para os documentos.
- **`.env.example`**: toda variável de ambiente usada, sem valores reais.

Docstrings claras nos módulos e funções públicas fazem parte da
documentação: registrar o que a função faz, não como ela faz.

Verificar que os documentos não se contradizem e que todo comando citado
existe de fato.

## Fase 5 — Testar

Elevar a rede de segurança do mínimo necessário para o padrão da área:

1. Confirmar que os testes de caracterização criados na implementação
   continuam passando.
2. Cobrir a jornada principal de cada feature pelo comportamento
   observável, não por detalhe interno.
3. Organizar `tests/` espelhando as features, testando `model.py`,
   `use_cases.py` e os adaptadores.
4. Testar `model.py` sem I/O: entrada, saída, limites e entrada inválida.
5. Cobrir as fronteiras com dublês em vez de disco e rede reais: falha de
   I/O, dado inválido, ausência de dado e permissão negada.
6. Testar a GUI por casos de uso, controladores ou janelas falsas, sem
   depender de display real na suíte padrão.
7. Garantir um comando único que roda os testes.

Não perseguir cobertura por número. Cobrir o que quebraria sem alarme.

## Fase 6 — Validar

Fechar o ciclo com verificação automatizada:

1. Garantir que existam tarefas para formatação, lint, checagem de tipos,
   testes e empacotamento, agrupadas em um único comando de validação.
2. Garantir que a checagem de tipos cubra o código migrado e registrar,
   se necessário, o plano para chegar ao modo estrito.
3. Adicionar uma verificação executável das fronteiras entre features,
   `shared` e composições de interface, para que a organização não se
   degrade com o tempo.
4. Rodar a validação completa até ficar tudo verde.
5. Comparar com a linha de base da Fase 1 e confirmar que nada
   regrediu.
6. Revisar o diff final por inteiro, incremento por incremento.

Se a validação exigir configuração nova, mantê-la mínima, declarada no
`pyproject.toml` e coerente com o ferramental existente.

## Encerramento

Relatar ao usuário:

- o que o projeto faz, conforme documentado;
- estrutura antes e depois;
- incrementos aplicados e commits gerados;
- documentos criados ou atualizados;
- resultado da validação comparado à linha de base;
- itens deixados fora do escopo, com encaminhamento proposto;
- pontos do `docs/prd.md` inferidos do código que ainda precisam de
  confirmação;
- próximo passo recomendado: usar `plan-feature` para a próxima demanda,
  agora dentro do padrão.

Não implementar features novas nesta skill.
