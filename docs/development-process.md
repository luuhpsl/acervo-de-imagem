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
11. **Verificação automática**: aguarde o CI; ele repete o `validate` nas versões e sistemas suportados.
12. **Revisão**: ajuste conforme os comentários antes de integrar.

## Proteções recomendadas no GitHub

Depois de criar um repositório a partir do template:

1. Em **Settings > Rules > Rulesets**, proteja a branch padrão.
2. Exija pull request, ao menos uma aprovação e resolução das conversas.
3. Exija os checks dos workflows `CI` e `Security` antes do merge.
4. Impeça force push e exclusão da branch padrão.
5. Em **Settings > Security**, habilite dependency graph, Dependabot alerts,
   Dependabot security updates e private vulnerability reporting.

Essas opções são configurações do repositório no GitHub e não podem ser ativadas
somente por arquivos versionados. Pull requests do Dependabot passam pelo mesmo CI e
pela mesma revisão; não há merge automático.

## Ambiente

- Crie o ambiente com `uv sync` (recomendado) ou `python -m venv .venv` + `pip install -e ".[dev]"`.
- A versão do Python recomendada está em `.python-version`.
- O `uv.lock` deve ser versionado para builds reproduzíveis.
- Instale os hooks com `uv run pre-commit install` para antecipar o retorno do CI.

## Verificação automática

Dois workflows rodam no GitHub Actions:

| Workflow    | Quando                              | O que faz                                                             |
| ----------- | ----------------------------------- | --------------------------------------------------------------------- |
| `ci`        | push, Pull Request                  | `validate` em Python 3.13 × Linux/Windows, e `pre-commit`               |
| `security`  | push, Pull Request, semanalmente    | `pip-audit` sobre o `uv.lock` e `gitleaks` sobre o histórico            |

O `validate` é a porta local e permanece **offline**. Duas verificações dependem de rede e por isso ficam fora dele:

- `python scripts/dev.py audit` — vulnerabilidades nas dependências.
- `python scripts/dev.py check-workflows` — validade dos workflows do GitHub Actions.

A segunda roda automaticamente no pre-commit quando você toca em `.github/workflows/`. Ela precisa acontecer **antes do push**: um workflow inválido não falha no CI, ele simplesmente não chega a iniciar — e um `ci.yml` quebrado não consegue se auto-verificar.

## Dependências e segurança

- Toda dependência nova é justificada no Pull Request e registrada em um ADR quando for de runtime.
- `python scripts/dev.py audit` confere o `uv.lock` contra o banco de vulnerabilidades; o CI repete semanalmente.
- Segredos nunca vão para o repositório: o hook do `gitleaks` bloqueia no commit e o CI varre o histórico.
- Valores locais ficam em `.env.local`, sempre fora do Git.

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
