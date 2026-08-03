# AGENTS.md

Instruções para agentes de IA que forem trabalhar neste repositório.

Este projeto é uma aplicação desktop Python/Tkinter para catalogação de acervo visual com OpenAI, Firebase Storage e Firestore. O objetivo dos agentes é implementar ajustes com segurança, preservar dados, manter a interface estável e evitar custos desnecessários de API.

## Leitura obrigatória antes de alterar código

1. `README.md`
2. `Documentos/Doc/visao-geral.md`
3. `Documentos/Doc/arquitetura.md`
4. `Documentos/Doc/uso.md`
5. Arquivos diretamente afetados pela tarefa

## Arquivos principais

- `src/acervo_visual_inteligente/gui.py`: interface principal Tkinter.
- `src/acervo_visual_inteligente/catalogo_logic.py`: regras de negócio, varredura, metadados, upload, filas e Firestore.
- `src/acervo_visual_inteligente/auth_server.py`: autenticação local.
- `src/acervo_visual_inteligente/index.html`: vitrine/local preview.
- `src/acervo_visual_inteligente/Icons - Programa/`: ícones oficiais da interface.
- `storage.rules`: regras de Firebase Storage.
- `Documentos/Doc/`: documentação operacional do projeto.

## Regras de segurança

- Nunca exponha, imprima ou comite chaves de API, tokens, credenciais Firebase ou arquivos `.env.local`.
- Não altere regras de Storage/Firestore sem explicar impacto e pedir confirmação quando houver risco.
- Não envie arquivos reais do acervo para terceiros.
- Não apague filas JSON automaticamente sem ação explícita do usuário.
- Evite qualquer fluxo que faça chamadas extras à OpenAI sem necessidade clara.
- Se uma correção puder ser feita localmente sem nova chamada à API, prefira a correção local.

## Versionamento

- Toda alteração visível ao usuário deve atualizar a versão em:
  - `src/acervo_visual_inteligente/__init__.py`
  - fallback de versão em `src/acervo_visual_inteligente/gui.py`, se existir
  - `tests/test_package_metadata.py`
  - cópia legada `meu_catalogo_continuacao/main.py`, quando o ajuste ainda precisar ser espelhado
- Use versionamento incremental:
  - patch: correção pequena ou ajuste visual
  - minor: novo recurso relevante
  - major: mudança incompatível

## Interface

- Preserve o estilo retrô/Windows 98.
- Mantenha tooltips nos botões.
- Não remova botões existentes sem pedido explícito.
- Ícones devem vir de `src/acervo_visual_inteligente/Icons - Programa/`.
- A cópia antiga pode existir, mas a pasta central de ícones deve ser a do projeto principal.
- Evite bloquear a janela com operações longas. Varredura, upload, conversão e OpenAI são candidatos a thread/fila.

## Filas JSON

Fluxos esperados:

- `pending_metadata.json`: arquivos que falharam e precisam de reprocessamento.
- `processing_queue.json`: fila/checkpoint atual do processamento.
- Futuro desejado:
  - `lista_completa_de_varredura.json`
  - `lista_materiais_interrompidos.json`
  - `arquivos_metadata_pendentes.json`

Ao alterar filas:

- Use escrita atômica: grave em `.tmp` e substitua com `os.replace`.
- Preserve caminhos originais.
- Não descarte itens sem registrar no log.
- Em queda de energia, o usuário deve conseguir retomar.

## OpenAI

- Modelo atual do fluxo: `gpt-4o-mini`.
- Use `detail: low` para reduzir custo.
- Não implemente retry automático caro sem aprovação.
- Para erro de JSON da IA, prefira correção local de JSON quando seguro.
- Se precisar consultar preço/modelo atual, use apenas fontes oficiais da OpenAI.

## Firebase

Estrutura esperada no Storage:

```text
acervo-visual-unificado/
├── thumbnails/{origem}/{ano}/IMG-{ano}-{sequencial}.jpg
└── originals/
    ├── raster/{origem}/{ano}/IMG-{ano}-{sequencial}.{jpg|jpeg|png}
    └── vector/{origem}/{ano}/IMG-{ano}-{sequencial}.{eps|ai|svg}
```

Metadados ficam no Firestore e devem conter caminhos/URLs suficientes para ligar thumbnail, original e futuro site.

## Duplicidade e variações

- SHA-256 identifica arquivo idêntico.
- pHash identifica imagem visualmente semelhante.
- Se houver PB e colorida da mesma imagem, a colorida deve prevalecer.
- Se só existir PB, a PB pode ser enviada.
- Se uma colorida aparecer depois de uma PB já processada, a colorida também deve ser mantida.
- Se uma PB aparecer depois de uma colorida equivalente, a PB deve ser ignorada como duplicada.

## Validação mínima

Antes de entregar alterações em Python:

```powershell
python -m py_compile src\acervo_visual_inteligente\gui.py src\acervo_visual_inteligente\catalogo_logic.py src\acervo_visual_inteligente\auth_server.py
```

Quando dependências de dev estiverem instaladas:

```powershell
python -m pytest
```

Se `pytest` não estiver instalado, informe isso no resumo e rode validação equivalente quando possível.

## Git

- Verifique o estado antes de alterar:

```powershell
git status --short --branch
```

- Preserve alterações existentes do usuário.
- Não use `git reset --hard`.
- Não force push.
- Remote oficial:

```text
https://github.com/DevEdTech/Acervo-de-Imagens.git
```

## Estilo de entrega

Ao finalizar:

- Explique o resultado.
- Liste arquivos alterados.
- Informe validações executadas.
- Aponte pendências ou riscos reais.
- Seja direto e em português.
