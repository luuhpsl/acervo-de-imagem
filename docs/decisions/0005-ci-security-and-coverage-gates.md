# ADR 0005 — Verificação contínua, segurança de suprimentos e cobertura aplicada

## Contexto

O [ADR 0004](0004-local-reliability-tooling.md) deixou CI/CD fora do escopo: o `validate` local era a única porta de qualidade. Uma revisão do estado do projeto mostrou o custo dessa escolha e outros pontos que dependiam apenas de disciplina:

- Nada impedia integrar código que nunca passou pelo `validate`; o processo descrito em `CONTRIBUTING.md` pressupunha uma verificação que não existia.
- O `requires-python` prometia 3.11+, mas nenhuma versão além da local era exercitada.
- O `validate` falhava em um clone novo, porque as cópias de skills são ignoradas pelo Git e a conferência vinha antes da sincronização.
- O limite de cobertura (`fail_under = 80`) estava configurado mas nunca aplicado — o `validate` rodava o pytest sem `--cov`, e a cobertura real era de 65%.
- "Nunca faça commit de segredos" e a política de dependências enxutas eram regras de texto, sem verificação.
- Um lock deixado por um processo morto tornava as notas permanentemente somente-leitura, com uma mensagem pedindo para tentar de novo.

## Decisão

- Adotar GitHub Actions com dois workflows: `ci` (`validate` em Ubuntu e Windows, mais `pre-commit`) e `security` (auditoria de dependências e varredura de segredos, também semanal).
- Padronizar **uma única versão de Python (3.13)** em `requires-python`, `.python-version`, no alvo do mypy e no CI. Testar um intervalo (`>=3.11`) exigiria exercitar as duas pontas; declarar o intervalo e testar só uma ponta recriaria o problema que este ADR resolve — uma promessa sem verificação. A matriz varia apenas o sistema operacional, onde o template de fato promete comportamento idêntico e há código sensível (caminhos de dados por SO, `fsync` de diretório, locks de arquivo).
- Rodar todas as ferramentas Python do `pre-commit` através do `dev.py`, sem `rev` própria. Um hook com versão fixa introduz uma segunda versão do ruff, que diverge da do `uv.lock` e reprova código que o `validate` aprova.
- Rodar `sync-skills` antes de `check-skills` dentro do `validate`, tratando as cópias como artefato gerado — um clone novo fica verde.
- Aplicar de fato o limite de cobertura, rodando o pytest com `--cov` no `validate`.
- Excluir da medição de cobertura apenas as funções que exigem display real (`build_window`, `create_*_panel`), coerente com a regra de que adaptadores gráficos não contêm lógica.
- Auditar o `uv.lock` com `pip-audit` executado via `uvx`, sem acrescentar dependência de desenvolvimento.
- Detectar segredos com `gitleaks`, no pre-commit (prevenção) e sobre o histórico no CI (detecção).
- Estender o pre-commit para rodar mypy e pytest, alinhando-o ao gate do CI.
- Tornar o lock de escrita recuperável: quem o detém registra PID e horário, e um lock além do TTL é tratado como abandonado.
- Gravar com `fsync` antes da troca atômica e registrar datas com fuso explícito (UTC).

## Consequências

O `validate` continua sendo a porta local e permanece offline: a auditoria depende de rede e fica fora dele, coberta pelo CI e pelo agendamento semanal. A verificação passa a ser obrigatória, e não opcional, o que substitui a consequência registrada no ADR 0004.

A exclusão de cobertura das funções gráficas é uma fronteira que precisa ser respeitada: se lógica migrar para dentro delas, deixa de ser medida. A revisão e o `check-architecture` seguem responsáveis por mantê-las finas.

O TTL do lock (30 segundos) assume operações curtas. Uma feature que segure o lock por mais tempo precisa revisar esse valor.

Fixar o Python em 3.13 é o custo consciente de manter promessa e verificação alinhadas: quem estiver em 3.11 ou 3.12 não instala mais o template. Voltar a suportar um intervalo é possível, desde que a matriz volte a exercitar as duas pontas junto com a mudança em `requires-python`.

`shared/types.py` (`Ok`/`Err`/`Result`) foi removido por não ter uso, seguindo a regra de não manter abstração sem necessidade demonstrada.
