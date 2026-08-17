# Trabalhando com agentes

Este template foi feito para ser usado com agentes de código. Aqui está como orientá-los.

## Prompts x arquivos persistentes

- **Prompt**: o que você pede no momento, para uma tarefa específica ("crie um subcomando para exportar um CSV").
- **Arquivos persistentes**: regras que valem sempre, gravadas no repositório:
  - `AGENTS.md` (raiz) — regras gerais para qualquer agente.
  - `CLAUDE.md` (raiz) — instruções específicas para o Claude Code.

O agente lê os arquivos persistentes automaticamente. Use o prompt para a tarefa; deixe as regras fixas nos arquivos.

## Skills disponíveis

- **plan-app** — entrevista pessoas não desenvolvedoras até transformar uma ideia em um PRD aprovado, com escopo, não escopo e decisões de arquitetura explícitas.
- **save-legacy-project** — analisa um projeto legado sem documentação e produz um plano aprovado de reestruturação em features, com documentação completa, sem mudar o comportamento.
- **plan-feature** — planeja uma funcionalidade antes de escrever código.
- **implement-feature** — implementa a funcionalidade seguindo o plano e a arquitetura.
- **review-changes** — revisa as alterações feitas.
- **generate-tests** — gera testes para o comportamento implementado.
- **update-documentation** — atualiza a documentação após uma mudança.
- **prepare-pull-request** — organiza commit e descrição do Pull Request.

As skills canônicas ficam em `/skills`; as cópias em `.claude/skills` e `.agents/skills` são geradas por `python scripts/dev.py sync-skills`.

## Como definir o produto

Use `plan-app` quando ainda existe uma ideia, mas não um produto completamente decidido. Ela também define se a experiência será CLI, GUI ou ambas. A skill faz perguntas curtas, explica escolhas sem exigir conhecimento técnico e não começa a implementação. Quando não restar nenhuma decisão necessária em aberto, ela pede a aprovação do resumo, cria `docs/prd.md` e atualiza `docs/architecture.md`.

> Use a skill plan-app para me ajudar a definir uma ferramenta que organiza automaticamente os arquivos recebidos pela minha equipe.

Ao responder, evite tentar escrever uma especificação técnica. Explique o problema e escolha entre as alternativas apresentadas; a skill transforma as respostas em requisitos verificáveis.

## Como resgatar um projeto legado

Use `save-legacy-project` quando o projeto já existe, mas não tem documentação nem organização de pastas. A skill inspeciona o repositório, apresenta um diagnóstico e propõe um plano de reestruturação em incrementos reversíveis. Ela só implementa depois da sua aprovação e não muda o comportamento do sistema.

> Use a skill save-legacy-project para analisar este projeto e propor um plano de reestruturação no padrão da área.

## Como pedir planejamento

> Use a skill plan-feature para planejar um subcomando que lê um arquivo CSV e imprime um resumo.

## Como pedir revisão

> Use a skill review-changes para revisar o que foi alterado nesta branch.

## Limites de autonomia

O agente deve:

- Não expandir o escopo além do que foi pedido.
- Não instalar dependências sem justificar a necessidade (o template preza por zero dependências de runtime).
- Não expor segredos nem colocar credenciais no código.
- Não mudar a arquitetura sem explicar o motivo e registrar a decisão em um ADR (`docs/decisions/`).

Na dúvida, o agente deve perguntar antes de agir.
