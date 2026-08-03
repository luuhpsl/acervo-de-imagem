# Arquitetura

O projeto usa uma estrutura Python com pacote instalável em `src/acervo_visual_inteligente`.

## Estrutura resumida

```text
src/acervo_visual_inteligente/
├── __init__.py
├── __main__.py
├── auth_server.py
├── catalogo_logic.py
├── gui.py
├── index.html
├── acervo.ico
├── Font/
└── Icons - Programa/
```

## Responsabilidades

### `gui.py`

Controla a interface gráfica:

- janela principal;
- tema claro/escuro;
- botões e tooltips;
- barra de progresso;
- log visual;
- cards de métricas;
- botão de carregar JSON;
- integração entre interface e lógica.

### `catalogo_logic.py`

Contém o motor principal:

- autenticação auxiliar;
- varredura de pastas;
- filtragem por origem e extensão;
- hash SHA-256;
- pHash;
- preferência entre colorida/PB;
- conversão de vetores;
- geração de thumbnail;
- chamada OpenAI;
- upload Firebase Storage;
- gravação Firestore;
- fila de processamento;
- pendências.

### `auth_server.py`

Servidor Flask local usado no fluxo de autenticação.

### `index.html`

Vitrine simples/local para visualizar dados exportados ou simular consulta.

## Fluxo de processamento

```text
Selecionar pasta
→ Varredura recursiva
→ Filtro por prefixo/extensão
→ Remoção/preferência de variações
→ Criação/salvamento da fila
→ Play
→ Para cada arquivo:
    → hash SHA-256
    → pHash
    → conversão se vetor
    → thumbnail
    → OpenAI Vision
    → upload thumbnail
    → upload original
    → gravação Firestore
    → atualização de checkpoint
```

## Firebase Storage

Estrutura recomendada:

```text
acervo-visual-unificado/
├── thumbnails/
│   └── {origem}/{ano}/IMG-{ano}-{sequencial}.jpg
└── originals/
    ├── raster/
    │   └── {origem}/{ano}/IMG-{ano}-{sequencial}.{jpg|jpeg|png}
    └── vector/
        └── {origem}/{ano}/IMG-{ano}-{sequencial}.{eps|ai|svg}
```

## Firestore

Cada documento deve guardar:

- nome original;
- nome amigável/sequencial;
- origem;
- extensão;
- tipo do arquivo original;
- resolução;
- tamanho;
- hash SHA-256;
- pHash;
- característica de cor;
- URL/caminho do original;
- URL/caminho da thumbnail;
- metadados gerados pela IA;
- datas de processamento.

## Pontos de atenção

- A varredura de pastas muito grandes pode travar a GUI se permanecer no thread principal.
- A comparação pHash lendo toda a coleção do Firestore pode escalar mal em acervos grandes.
- Chamadas extras à OpenAI aumentam custo.
- Arquivos vetoriais gigantes precisam de limite de resolução na conversão.
