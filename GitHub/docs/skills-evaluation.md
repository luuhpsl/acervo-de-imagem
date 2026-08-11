# Avaliação de Skills

Este documento serve como guia para avaliar se um agente de IA está usando as skills corretamente. Para cada skill, há um prompt de exemplo, critérios de qualidade e sinais de alerta.

Use-o para calibrar expectativas ao testar um novo agente, modelo ou configuração.

---

## plan-app

**Propósito**: Conduzir da ideia inicial até um PRD aprovado, sem implementar código.

**Prompt de exemplo**:
```text
Use a skill plan-app. Quero criar uma ferramenta CLI que monitore o uso de disco em diretórios especificados, alerte quando o uso passar de um limite, e salve o histórico em arquivo local.
```

**Bom resultado**:
- Fez perguntas curtas em rodadas (1 a 3 por vez), não um questionário longo
- Rejeitou termos vagos ("simples", "intuitivo") pedindo exemplos ou limites concretos
- Seguiu a sequência de descoberta: problema → usuário → jornada → escopo → interface (CLI/GUI) → dados → SO → distribuição
- Perguntou se o produto será CLI, GUI ou ambas
- Apresentou resumo final e pediu aprovação explícita antes de gerar arquivos
- Gerou `docs/prd.md` com IDs estáveis (RF-01, CA-01) e sem "TBD" ou "a definir"
- Atualizou `docs/architecture.md` com seção `Decisões do produto` sem contradizer o PRD
- Nenhum código foi implementado

**Sinais de alerta**:
- Aceitou "quero algo simples" sem pedir definição concreta
- Criou código ou funções junto com o PRD
- Deixou itens marcados como TBD, "a definir" ou "etc."
- Não pediu aprovação explícita antes de gerar os documentos
- Inventou requisitos que o usuário não mencionou
- Não verificou se a stdlib resolve antes de propor dependências

---

## save-legacy-project

**Propósito**: Diagnosticar um projeto legado e produzir um plano aprovado de reestruturação, sem mudar o comportamento.

**Prompt de exemplo**:
```text
Use a skill save-legacy-project. Herdei um projeto com quinze scripts soltos na raiz, sem testes nem documentação, que lê planilhas e envia relatórios por e-mail.
```

**Bom resultado**:
- Inspecionou o repositório e rodou os comandos existentes antes de propor qualquer mudança
- Registrou a linha de base, distinguindo o que já falhava do que poderia regredir
- Apresentou diagnóstico curto: o que o projeto faz, como está organizado e os maiores problemas
- Mapeou cada capacidade para uma feature e deu destino a todos os arquivos, sem sobras
- Separou, por módulo, o que é regra pura, I/O, orquestração e interface
- Propôs incrementos pequenos e reversíveis, começando pela rede de segurança
- Pediu aprovação explícita antes de mover qualquer arquivo
- Escreveu testes de caracterização antes de mover código descoberto
- Usou `git mv`, com um commit por incremento
- Marcou como dúvida o que o código não permitia concluir, em vez de supor

**Sinais de alerta**:
- Começou a mover arquivos antes da aprovação do plano
- Reescreveu regras de negócio ou corrigiu bugs junto com a movimentação
- Deixou arquivos sem destino definido no plano
- Misturou vários incrementos em um único commit
- Adicionou dependências ou trocou o toolkit gráfico durante o resgate
- Inventou objetivos de produto no `docs/prd.md` em vez de reconstruir o comportamento existente
- Tratou uma falha que já existia na linha de base como regressão, ou o contrário
- Aproveitou o resgate para incluir features novas

---

## plan-feature

**Propósito**: Transformar uma solicitação em um plano claro antes de escrever código.

**Prompt de exemplo**:
```text
Use a skill plan-feature para planejar a funcionalidade de alerta configurável: o usuário define o limite de uso de disco (em %) e o diretório a monitorar via argumentos da CLI.
```

**Bom resultado**:
- Leu `AGENTS.md` e `docs/architecture.md` antes de planejar
- Identificou objetivo, requisitos e critérios de aceite
- Identificou os módulos envolvidos (`model`, `services`, `use_cases`, `commands`)
- Verificou se a stdlib resolve antes de propor dependências
- Propôs a solução mínima (sem over-engineering)
- Dividiu o trabalho em tarefas pequenas e sequenciais
- Listou riscos de portabilidade entre SOs
- Nenhum arquivo foi alterado

**Sinais de alerta**:
- Começou a implementar sem apresentar o plano
- Propôs uma solução complexa sem justificar
- Não separou lógica pura de I/O na proposta
- Ignorou restrições da arquitetura documentada
- Adicionou dependências externas sem verificar a stdlib

---

## implement-feature

**Propósito**: Executar uma tarefa planejada com alterações mínimas e verificadas.

**Prompt de exemplo**:
```text
O plano para a feature de alerta de disco foi aprovado. Use a skill implement-feature para executar.
```

**Bom resultado**:
- Declarou os arquivos que seriam alterados antes de começar
- Manteve as alterações estritamente dentro do escopo aprovado
- Lógica pura em `model.py`, I/O em `services.py`, orquestração em `use_cases.py`
- CLI e GUI como adaptadores finos dos mesmos casos de uso
- Usou type hints em todo código novo
- Adicionou ou atualizou testes de comportamento
- Executou `python scripts/dev.py validate` e passou limpo
- Revisou o diff final e listou limitações conhecidas

**Sinais de alerta**:
- Expandiu o escopo além do planejado ("já aproveitei e fiz X também")
- Colocou lógica de negócio no `commands.py` ou `gui.py`
- Colocou I/O no `model.py`
- Não adicionou testes
- Não executou o `validate`
- Importou módulos internos de outra feature (quebrou encapsulamento)
- Bloqueou o loop de eventos da GUI com operação demorada

---

## generate-tests

**Propósito**: Criar ou atualizar testes (pytest) cobrindo o comportamento observável.

**Prompt de exemplo**:
```text
Use a skill generate-tests para adicionar testes à feature de alerta de disco.
```

**Bom resultado**:
- Testou o resultado observável, não detalhes internos de implementação
- Cobriu casos de sucesso e de falha
- Testes colocados em `tests/features/<nome>/`, espelhando a feature
- Reutilizou fixtures (`isolated_data_dir`, `tmp_path`, `monkeypatch`)
- Testou GUI via controladores/use-cases sem abrir janela real
- Não removeu nem enfraqueceu testes existentes
- Suíte de testes passou por completo

**Sinais de alerta**:
- Testou implementação interna (ex: "verifica se json.dumps foi chamado")
- Testes frágeis que quebram com refatoração sem mudança de comportamento
- Ignorou cenários de erro ou estados vazios
- Removeu ou alterou testes que estavam passando
- Testes que dependem de display/GUI real

---

## review-changes

**Propósito**: Revisar o diff antes de concluir uma tarefa.

**Prompt de exemplo**:
```text
Use a skill review-changes para revisar as alterações da feature de alerta.
```

**Bom resultado**:
- Verificou critérios de aceite, escopo e arquitetura
- Organizou achados em categorias: Bloqueador, Importante, Melhoria, Observação
- Confirmou que `model.py` permaneceu puro (sem I/O)
- Verificou portabilidade (uso de `pathlib`, sem caminhos fixos)
- Verificou type hints e se o mypy passa
- Identificou código morto, duplicação ou dependências desnecessárias
- Confirmou que não há segredos expostos
- Propôs correções mínimas sem alterar arquivos

**Sinais de alerta**:
- Disse "tudo está ótimo" sem analisar o diff
- Não categorizou os achados por prioridade
- Sugeriu mudanças fora do escopo da tarefa
- Ignorou questões de portabilidade ou segurança

---

## prepare-pull-request

**Propósito**: Gerar uma descrição clara de PR após a revisão.

**Prompt de exemplo**:
```text
Use a skill prepare-pull-request para preparar o PR da feature de alerta.
```

**Bom resultado**:
- Incluiu: Contexto, Objetivo, Alterações, Como Testar, Evidências, Limitações, Riscos
- Checklist completo e marcado (critérios, testes, lint, typecheck, build, docs, segredos, diff)
- Instruções de teste claras e reproduzíveis
- Evidências incluídas (logs de validação)

**Sinais de alerta**:
- Descrição genérica ("implementa feature X")
- Checklist incompleto ou com itens desmarcados sem explicação
- Sem instruções de como testar
- Sem evidências de validação

---

## update-documentation

**Propósito**: Manter a documentação coerente com o código.

**Prompt de exemplo**:
```text
Use a skill update-documentation após a implementação da feature de alerta.
```

**Bom resultado**:
- Verificou e atualizou comandos documentados (`scripts/dev.py`)
- Atualizou `.env.example` se novas variáveis foram adicionadas
- Atualizou `docs/architecture.md` se a estrutura mudou
- Verificou `docs/building.md` se o empacotamento foi afetado
- Criou ADR em `docs/decisions/` para decisões arquiteturais relevantes
- Listou documentos atualizados com resumo das mudanças

**Sinais de alerta**:
- Não verificou se os comandos documentados ainda funcionam
- Ignorou mudanças em variáveis de ambiente
- Não criou ADR para decisão arquitetural significativa
- Copiou trechos inteiros de código para a documentação
