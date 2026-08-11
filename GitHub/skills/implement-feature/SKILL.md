---
name: implement-feature
description: Use para implementar uma tarefa já planejada, mantendo as alterações dentro do escopo e validando o resultado.
---

# Implementar funcionalidade

## Finalidade

Implementar uma tarefa já planejada, com alterações mínimas e
verificadas.

## Quando usar

- Após o planejamento (plan-feature), quando o escopo está claro.
- Para executar uma tarefa específica dentro do escopo aprovado.

## Processo

1. Confirme os critérios de aceite da tarefa.
2. Declare os arquivos que serão alterados antes de começar.
3. Limite as alterações ao escopo da tarefa.
4. Não expanda o escopo nem antecipe trabalho futuro.
5. Reutilize os padrões e módulos já existentes.
6. Mantenha a lógica pura em `model.py`, o I/O em `services.py` e a orquestração compartilhada em `use_cases.py`.
7. Mantenha CLI e GUI como adaptadores finos dos mesmos casos de uso; não duplique regra de negócio.
8. Não bloqueie o loop de eventos da GUI com trabalho demorado.
9. Use type hints em todo código novo.
10. Adicione ou atualize os testes de comportamento afetados.
11. Execute `python scripts/dev.py validate`.
12. Revise o diff final.

## Resultado esperado

- Lista de arquivos alterados.
- Resumo das mudanças.
- Resultado das validações (`python scripts/dev.py validate`).
- Limitações ou pendências conhecidas.
