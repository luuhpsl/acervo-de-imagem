---
name: generate-tests
description: Use para criar ou atualizar testes com base no comportamento observável de uma feature.
---

# Gerar testes

## Finalidade

Criar ou atualizar testes (pytest) que cubram o comportamento observável
do código.

## Quando usar

- Ao adicionar ou alterar comportamento.
- Quando a cobertura de um caso relevante está ausente.

## Processo

1. Identifique o comportamento observável a ser testado.
2. Teste o resultado observável, não os detalhes internos.
3. Cubra os casos de sucesso e de falha.
4. Não remova nem enfraqueça testes existentes.
5. Coloque os testes em `tests/`, espelhando a estrutura da feature e cobrindo os casos de uso compartilhados.
6. Reutilize fixtures existentes (ex.: `isolated_data_dir` para persistência).
7. Use `tmp_path`/`monkeypatch` para isolar I/O.
8. Para GUI, teste controladores, casos de uso e fábricas injetadas sem abrir uma janela real na suíte padrão.
9. Execute a suíte de testes (`python scripts/dev.py test`).

## Resultado esperado

- Testes adicionados ou atualizados.
- Resultado da execução da suíte.
