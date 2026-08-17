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

Estrutura única:

```text
acervo-visual-unificado/{uuid}/
├── {uuid}_original.{extensao}
├── {uuid}_large.jpg
├── {uuid}_medium.jpg
└── {uuid}_thumb.jpg
```

O documento correspondente fica diretamente em
`acervo-visual-unificado/{uuid}` no Firestore. Não existem caminhos alternativos
por origem, ano ou tipo de arquivo.

## Firestore

Cada documento guarda nome original, origem, extensão, orientação, SHA-256,
pHash, área do conhecimento, tipo visual, de uma a cinco cores, descrição,
exatamente 15 palavras-chave e os caminhos/URLs de original, large, medium e
thumb. A chave numérica do fornecedor não é persistida.

## Pontos de atenção

- A varredura de pastas muito grandes pode travar a GUI se permanecer no thread principal.
- A comparação pHash lendo toda a coleção do Firestore pode escalar mal em acervos grandes.
- Chamadas extras à OpenAI aumentam custo.
- Arquivos vetoriais gigantes precisam de limite de resolução na conversão.
