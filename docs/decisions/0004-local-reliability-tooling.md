# ADR 0004 — Confiabilidade local do template

## Contexto

O template precisa validar personalização, persistência e distribuição sem depender de CI/CD ou de novas dependências de runtime.

## Decisão

- Tornar o setup idempotente, transacional, revisável por dry-run e responsável pela seleção real de interfaces.
- Versionar a persistência de notas, migrar o legado e proteger gravações com lock e revisão otimista.
- Validar links e comandos documentados no fluxo local.
- Fornecer um gerador mínimo de feature compatível com as interfaces disponíveis.
- Instalar e executar o wheel em um ambiente virtual limpo após o build.

## Consequências

O `validate` fica mais abrangente e um pouco mais lento, mas verifica o artefato que será entregue. CI/CD permanece fora do escopo.
