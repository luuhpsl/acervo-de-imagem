# Política de segurança

## Versões com suporte

Este template recebe correções de segurança na versão presente na branch padrão.
Projetos criados a partir de versões anteriores devem incorporar as atualizações do
template conforme [docs/updating.md](docs/updating.md).

## Reportar uma vulnerabilidade

Não abra uma issue pública com detalhes de uma possível vulnerabilidade.

1. Na página do repositório no GitHub, abra **Security**.
2. Selecione **Report a vulnerability** para criar um aviso de segurança privado.
3. Informe o impacto, os passos mínimos para reprodução, as versões afetadas e, se
   possível, uma sugestão de correção.

Se o relatório privado ainda não estiver habilitado no repositório derivado, entre
em contato privadamente com os mantenedores e inclua somente o mínimo necessário em
qualquer solicitação pública de contato.

Os mantenedores devem confirmar o recebimento em até cinco dias úteis, manter o
relator informado sobre a análise e coordenar a divulgação depois que uma correção
estiver disponível.

## Responsabilidade dos mantenedores

- Manter os alertas e as atualizações de segurança do Dependabot habilitados.
- Revisar pull requests de dependências; o template não faz merge automático.
- Revogar e substituir imediatamente qualquer segredo exposto.
- Publicar uma correção e orientar os usuários sobre versões afetadas quando a
  vulnerabilidade for confirmada.
