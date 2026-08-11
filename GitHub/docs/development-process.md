# Processo de desenvolvimento

Fluxo recomendado para levar uma ideia até o código, de forma organizada e verificável.

## Fluxo

1. **Descoberta do produto**: se a ideia ainda estiver vaga, use `plan-app`. Responda às perguntas até aprovar um escopo e um não escopo completos em `prd.md`.
2. **Demanda**: escolha uma capacidade aprovada no PRD e descreva o que se quer resolver e para quem.
3. **Especificação**: detalhe o comportamento esperado, entradas e saídas.
4. **Critérios de aceite**: liste, de forma objetiva, o que precisa ser verdade para a demanda estar pronta.
5. **Planejamento**: quebre em passos. Você pode pedir ao agente: "Use a skill plan-feature...".
6. **Branch**: crie uma branch para o trabalho (`git checkout -b feat/descricao`).
7. **Implementação**: escreva o código seguindo a [arquitetura](architecture.md).
8. **Validação local**: rode `python scripts/dev.py validate` até ficar tudo verde.
9. **Commit**: registre as mudanças com mensagem clara.
10. **Pull Request**: abra o PR descrevendo o que mudou e por quê.
11. **Revisão**: ajuste conforme os comentários antes de integrar.

## Ambiente

- Crie o ambiente com `uv sync` (recomendado) ou `python -m venv .venv` + `pip install -e ".[dev]"`.
- A versão do Python recomendada está em `.python-version`.
- O `uv.lock` deve ser versionado para builds reproduzíveis.

## Mensagens de commit

Use um prefixo de tipo:

```
feat: adiciona subcomando de exportação de relatório
fix: corrige caminho de dados no Windows
docs: documenta como configurar variáveis de ambiente
```

Outros prefixos úteis: `test:`, `refactor:`, `chore:`.

## Definição de concluído

Uma tarefa está concluída quando:

- Os critérios de aceite foram atendidos
- Funciona localmente
- Os testes passam
- Não há erro de lint, typecheck ou build (`python scripts/dev.py validate` verde)
- A documentação foi atualizada quando necessário
- As alterações estão registradas no Git
