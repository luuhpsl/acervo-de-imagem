---
name: update-documentation
description: Use para manter a documentação coerente com o código após mudanças de comandos, arquitetura, funcionalidades, integrações ou decisões.
---

# Atualizar documentação

## Finalidade

Manter a documentação em `docs/` coerente com o estado atual do
código.

## Quando usar

- Após mudanças que afetam comandos, arquitetura ou funcionalidades.
- Após decisões relevantes de projeto.

## Processo

1. Verifique se os comandos documentados continuam corretos (`scripts/dev.py`).
2. Verifique as variáveis de ambiente e o `.env.example`.
3. Verifique se a arquitetura descrita reflete o código.
4. Atualize a descrição das funcionalidades alteradas.
5. Verifique se entradas CLI/GUI e o guia de build (`docs/building.md`) seguem corretos.
6. Registre limitações conhecidas.
7. Registre decisões relevantes como ADR em `docs/decisions`.
8. Atualize a documentação de integrações externas.

## Resultado esperado

- Lista de documentos atualizados.
- Resumo do que mudou em cada um.
