# Atualizando seu Projeto

Como este projeto foi criado a partir de um template, o template pode receber atualizações (novas configurações, atualizações do `uv`, regras do `ruff`).

Para trazer essas atualizações para o seu projeto sem perder suas modificações:

1. Adicione o repositório do template como um _remote_:
   `git remote add template https://github.com/DevEdTech/template-ia-python.git`
2. Baixe as atualizações:
   `git fetch template`
3. Faça o merge das alterações na sua branch atual (permitindo históricos diferentes na primeira vez):
   `git merge template/master --allow-unrelated-histories`
4. Resolva possíveis conflitos (geralmente no `README.md` ou `pyproject.toml`).
5. Faça um commit com a resolução.

## Atualizações automáticas de dependências

O arquivo `.github/dependabot.yml` agenda verificações semanais para:

- dependências Python gerenciadas por `uv`, mantendo `pyproject.toml` e `uv.lock`
  coerentes;
- GitHub Actions usadas pelos workflows.

Atualizações minor e patch são agrupadas para reduzir ruído. Atualizações major
continuam em pull requests separados para facilitar a avaliação de incompatibilidades.
Revise o changelog, confirme as mudanças no lockfile e só integre depois que o workflow
`CI` passar. Atualizações de segurança não devem ser adiadas apenas para esperar a
janela semanal.

As actions externas do workflow são fixadas por SHA completo e acompanhadas de um
comentário com a versão. O Dependabot mantém os dois sincronizados ao propor uma
atualização.
