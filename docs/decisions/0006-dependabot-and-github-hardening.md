# ADR 0006 — Dependabot e endurecimento dos workflows do GitHub

## Contexto

O ADR 0005 introduziu CI e verificações contínuas de segurança. O template também
precisa manter dependências e automações atualizadas sem depender de ações manuais
frequentes e reduzir o risco de alterações em actions referenciadas por tags móveis.

## Decisão

- Instalar dependências exclusivamente a partir do `uv.lock` no CI.
- Conceder ao `GITHUB_TOKEN` somente leitura de conteúdo, não persistir credenciais do
  checkout e limitar o tempo de execução dos jobs.
- Fixar actions externas por SHA completo e usar o Dependabot para propor suas
  atualizações.
- Usar o ecossistema `uv` do Dependabot para atualizar dependências Python e o
  lockfile, agrupando versões minor e patch.
- Exigir revisão humana: o template não aprova nem integra automaticamente pull
  requests de dependências.

## Consequências

Lockfiles desatualizados passam a bloquear a integração e os mantenedores precisam
revisar os pull requests gerados. Alertas, atualizações de segurança, proteção de
branch e reporte privado ainda precisam ser habilitados nas configurações de cada
repositório derivado.
