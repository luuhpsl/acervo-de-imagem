# Build e distribuição multiplataforma

O template entrega pacote Python e executáveis standalone para CLI ou GUI.

| Forma | Precisa de Python no destino? | Multiplataforma? | Quando usar |
| --- | --- | --- | --- |
| Wheel + sdist | Sim | Sim, para Python compatível | Instalação com pip/uv e distribuição para desenvolvedores |
| Executável CLI | Não | Um build por sistema | Terminal, automação e scripts |
| Executável GUI | Não | Um build por sistema | Aplicação desktop sem janela de console |

## Pacote Python

```bash
python scripts/dev.py build
```

O build gera wheel e sdist em `dist/` e, em seguida, instala o wheel mais recente em um ambiente virtual limpo, sem consultar índices ou instalar dependências. A importação e a entrada CLI, quando presente, são exercitadas. As entradas disponíveis refletem a escolha `cli`, `gui` ou `both` feita no setup.

## Executável CLI

```bash
python scripts/dev.py build-exe
# equivalente explícito:
python scripts/dev.py build-exe --interface cli
```

Saída padrão: `dist/app-template` ou `dist/app-template.exe`.

## Executável GUI

```bash
python scripts/dev.py build-exe --interface gui
```

Saída padrão: `dist/app-template-gui` ou `dist/app-template-gui.exe`. O build usa a opção windowed do PyInstaller, evitando uma janela de console ao abrir a GUI. O nome pode ser alterado:

```bash
python scripts/dev.py build-exe --interface gui --name meu-aplicativo
```

## Tkinter

Tkinter faz parte da biblioteca padrão do Python, mas algumas distribuições Linux o fornecem em pacote separado, como `python3-tk`. O build GUI deve ser executado em um ambiente onde Tkinter esteja disponível. A CLI e o pacote continuam utilizáveis sem carregar Tkinter.

## Sem cross-compilação

PyInstaller gera artefatos para o sistema e arquitetura atuais. Produzir um executável em cada ambiente de destino:

- Windows: arquivo `.exe`.
- macOS: binário específico de Intel ou Apple Silicon; assinatura e notarização ficam fora do escopo inicial.
- Linux: compatibilidade depende da glibc do ambiente de build; preferir uma distribuição-base antiga quando necessário.

## Versão e reprodutibilidade

A versão tem uma única fonte em `src/app_template/__init__.py`; o Hatch lê esse valor por `tool.hatch.version`. Versionar `uv.lock`, ou outro lockfile adotado, para builds reproduzíveis.
