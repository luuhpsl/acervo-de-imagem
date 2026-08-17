---
name: review-changes
description: Use para revisar alterações antes de concluir uma tarefa, verificando escopo, arquitetura, testes, segurança e qualidade.
---

# Revisar alterações

## Finalidade

Revisar o diff de uma tarefa antes de considerá-la concluída.

## Quando usar

- Antes de encerrar uma tarefa.
- Antes de preparar um pull request.

## Processo

1. Verifique se os critérios de aceite foram atendidos.
2. Verifique se as alterações ficaram dentro do escopo.
3. Verifique a aderência à arquitetura por features (`model`/`services`/`use_cases`/adaptadores de interface).
4. Confirme que `model.py` permaneceu puro (sem I/O).
5. Procure duplicação e código repetido.
6. Verifique se não foram adicionadas dependências desnecessárias.
7. Verifique se há type hints e se o mypy passa.
8. Procure erros de lógica e tratamento de falhas.
9. Verifique portabilidade (uso de `pathlib`, sem comandos de shell fixos).
10. Em GUI, verifique navegação por teclado, feedback de estado e se callbacks não bloqueiam o loop de eventos.
11. Verifique se há testes para o comportamento alterado sem dependência desnecessária de display.
12. Verifique se a documentação foi atualizada.
13. Confirme que não há segredos expostos.
14. Procure código não utilizado ou morto.
15. Não altere arquivos inicialmente; proponha correções mínimas.

## Resultado esperado

Achados organizados por prioridade:

- Bloqueador.
- Importante.
- Melhoria.
- Observação.
