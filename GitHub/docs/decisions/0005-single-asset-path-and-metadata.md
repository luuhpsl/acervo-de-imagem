# ADR 0005 — Caminho único e metadados controlados

## Contexto

O acervo possuía compatibilidade com caminhos antigos do Firestore e Storage,
além de metadados redundantes e verificações de similaridade que não percorriam
todas as páginas. Isso permitia inconsistências e imagens repetidas.

## Decisão

- Usar exclusivamente `acervo-visual-unificado/{uuid}` no Firestore e uma pasta
  de mesmo UUID no Storage.
- Derivar o UUID dos novos ativos do SHA-256 e reservar o documento antes do
  upload.
- Bloquear o envio quando a verificação de SHA-256 ou pHash falhar.
- Manter `chave_numeracao` apenas como cálculo transitório, sem persistência.
- Limitar os tipos visuais e a paleta de cores aos valores aprovados.
- Exigir 15 palavras-chave conceitualmente únicas; palavras de uso natural
  compartilhado entre português e inglês aparecem somente uma vez.

## Consequências

Os caminhos legados deixam de ser consultados e precisam ser inventariados
antes da publicação das novas regras. Reservas incompletas podem ser retomadas
após expirar, e a vitrine ignora documentos ainda sem URL de visualização. Não
há nova coleção, dependência ou chamada adicional à OpenAI.
