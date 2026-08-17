# Testes

## Filosofia

Testar o **comportamento observável**: entradas, saídas, arquivos produzidos e respostas às ações do usuário. Os testes devem continuar válidos quando a implementação interna mudar.

## Ferramenta

Usar pytest, configurado em `pyproject.toml`. A suíte padrão deve executar em ambiente headless, sem monitor ou servidor gráfico.

## Tipos de teste

- **Modelo**: regras puras de `model.py`.
- **Casos de uso**: orquestração de `model.py` e `services.py` compartilhada por todas as interfaces.
- **CLI**: parsing, saída, código de retorno e persistência.
- **GUI sem display**: entrada da aplicação, controladores e tratamento de indisponibilidade usando janelas ou dependências falsas.
- **GUI com display**: reservar para poucos testes de integração quando houver infraestrutura própria e valor comprovado.
- **Contrato local**: setup transacional, gerador de feature, documentação, arquitetura e wheel instalado.

## Localização

```
tests/
├── conftest.py
├── test_gui.py
└── features/
    └── minha-feature/
        ├── test_model.py
        ├── test_use_cases.py
        ├── test_commands.py
        └── test_gui.py        # quando existir lógica observável no adaptador
```

## Comandos

```bash
python scripts/dev.py test
python scripts/dev.py test-cov
python scripts/dev.py test -k nome_do_teste -v
```

## Cobertura

O `validate` roda o pytest com `--cov` e **falha abaixo de 80%**. O limite é um piso, não uma meta: cobertura alta com testes que verificam estado interno é pior do que cobertura menor com testes de comportamento.

Duas funções ficam fora da medição, marcadas com `# pragma: no cover`: `build_window` e `create_*_panel`. Elas só executam com display real, que a suíte padrão não usa. A contrapartida é uma fronteira a respeitar — **lógica não pode migrar para dentro delas**, ou deixa de ser medida e testada. Regra e orquestração pertencem ao controlador da feature (ex.: `NotesController`), que é testado sem widgets.

## Isolamento de I/O

Testes não devem tocar dados reais. Usar `tmp_path` e `monkeypatch` para redirecionar persistência e ambiente. A fixture `isolated_data_dir` já aponta os dados das features para uma pasta temporária.

## Testes de GUI

Não criar `Tk()` na suíte padrão. Separar regra e orquestração dos widgets, injetar uma fábrica de janela quando necessário e observar chamadas, estado apresentado ou mensagens de erro.

Exemplo:

```python
from app_template.gui import main


class FakeWindow:
    def __init__(self) -> None:
        self.started = False

    def mainloop(self) -> None:
        self.started = True


def test_gui_inicia_loop() -> None:
    window = FakeWindow()

    assert main(lambda: window) == 0
    assert window.started is True
```

Isso testa o contrato da entrada gráfica sem depender de display, resolução ou sistema operacional.

Controladores de feature, como `NotesController`, são testados sem widgets reais. O setup também é exercitado em uma cópia temporária: os testes cobrem dry-run, repetição idempotente, escolha real de interface, rollback, renomeação e remoção da demonstração. A persistência cobre migração, backup, lock e conflito de revisão. A validação final instala o wheel em um ambiente virtual temporário.

## O que não testar

- Estado interno ou nomes de variáveis.
- Detalhes do Tkinter, argparse ou bibliotecas de terceiros.
- Posição e cor puramente visuais sem impacto comportamental.
- Casos impossíveis apenas para aumentar cobertura.

## Investigar falhas

1. Ler a mensagem de erro e reproduzir o menor caso.
2. Rodar o teste específico com `-k` e `-v`.
3. Em falhas de GUI, distinguir erro de comportamento de indisponibilidade de display.
4. Atualizar o teste somente quando o comportamento mudou intencionalmente; caso contrário, corrigir o código.
