# Integrações e APIs

Como consumir dados externos e configurar o ambiente com segurança neste template.

## Consumo de APIs

Todo acesso a uma API passa por `services.py` dentro da feature. Os comandos e a lógica pura (`model.py`) nunca fazem I/O diretamente. Isso concentra a lógica de rede e o tratamento de erros em um só lugar e facilita usar dados fake nos testes.

Prefira a stdlib (`urllib.request`) para requisições simples. Só adote uma biblioteca como `httpx` ou `requests` se houver necessidade real — e registre a decisão em um ADR.

## Variáveis de ambiente

- Leia variáveis com `os.environ` **dentro de `services.py`**, nunca no `model`.
- Documente as variáveis necessárias em `.env.example`.
- Crie um `.env.local` para os valores do seu ambiente.
- **Nunca** faça commit de `.env` ou `.env.local`.

O template lê variáveis direto de `os.environ` (stdlib). Se você quiser carregar um arquivo `.env` automaticamente, `python-dotenv` é uma opção — mas é uma dependência de runtime, então registre a decisão em um ADR antes de adotá-la.

Exemplo em `.env.example`:

```
# APP_TEMPLATE_API_BASE_URL=https://api.exemplo.com
# APP_TEMPLATE_DATA_DIR=/caminho/para/dados
# APP_TEMPLATE_LOG_LEVEL=DEBUG
```

## Segredos

- Não coloque chaves de API, senhas ou tokens no código.
- Segredos vêm de variáveis de ambiente (ou de um cofre), lidos em `services.py`.
- Um executável PyInstaller **contém** todo o código empacotado; nunca embuta segredos nele.

A regra é verificada, não apenas documentada: o hook do `gitleaks` bloqueia um segredo no commit e o workflow `security` varre o histórico do repositório. Se um segredo já tiver sido commitado, **rotacione-o** — removê-lo do histórico não desfaz a exposição.

## Vulnerabilidades em dependências

`python scripts/dev.py audit` roda o `pip-audit` sobre o `uv.lock` — o que realmente é instalado. O CI repete a cada Pull Request e semanalmente, para que uma vulnerabilidade divulgada depois do merge ainda apareça. A ferramenta é executada via `uvx`, de forma efêmera, então auditar não acrescenta dependência ao ambiente de desenvolvimento.

## Portabilidade (Windows, macOS, Linux)

- Use `pathlib.Path` para caminhos; evite separadores fixos (`/` ou `\`).
- Para diretórios de dados/config do usuário, resolva o caminho por SO (veja `services.py` da feature `notes`) ou considere a lib `platformdirs` (dependência opcional, via ADR).
- Evite comandos de shell específicos de um SO. Prefira APIs da stdlib (`subprocess` com lista de argumentos, `shutil`).

## Tratamento de erros

No serviço, verifique se a operação foi bem-sucedida e traduza falhas em erros claros. Trate os estados explicitamente: **sucesso**, **vazio** e **erro**. Para a CLI, retorne um código de saída diferente de zero em caso de falha.

## Timeouts

Requisições de rede podem travar. Sempre defina um timeout (ex.: o parâmetro `timeout` de `urllib.request.urlopen`) para não deixar o processo esperando indefinidamente.

## Dados fake em desenvolvimento e testes

Para desenvolver ou testar sem depender de um recurso externo, injete uma implementação fake que respeite a mesma interface do serviço. Assim a aplicação funciona igual, e os testes ficam rápidos e previsíveis. A fixture `isolated_data_dir` já isola a persistência em disco nos testes.
