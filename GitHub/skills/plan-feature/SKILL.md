---
name: plan-feature
description: Use antes de implementar, para transformar uma solicitação em um plano — nova funcionalidade, mudança multi-arquivo, demanda ambígua, integração externa ou alteração arquitetural.
---

# Planejar funcionalidade

## Finalidade

Transformar uma solicitação em um plano claro antes de escrever ou
alterar qualquer código.

## Quando usar

- Nova funcionalidade.
- Mudança que afeta vários arquivos.
- Demanda ambígua ou incompleta.
- Integração com API ou serviço externo.
- Alteração arquitetural.

## Processo

1. Leia o `AGENTS.md` e a `docs/architecture.md`.
2. Identifique o objetivo e os critérios de aceite.
3. Liste os requisitos e as lacunas de informação.
4. Declare as suposições necessárias para prosseguir.
5. Identifique os módulos e features envolvidos (`model`, `services`, `use_cases`) e os adaptadores necessários (`commands` para CLI, `gui` para GUI).
6. Confirme quais interfaces fazem parte do escopo e proponha a solução mínima que atende ao objetivo.
7. Verifique se a stdlib resolve antes de propor qualquer dependência.
8. Divida o trabalho em tarefas pequenas e sequenciais.
9. Liste os riscos e os pontos de atenção (inclusive portabilidade entre SOs).
10. Não altere arquivos nesta etapa.

## Resultado esperado

- Resumo do objetivo.
- Requisitos.
- Não escopo (o que fica de fora).
- Suposições.
- Proposta de solução.
- Tarefas sequenciais.
- Riscos.
- Critérios de aceite.
