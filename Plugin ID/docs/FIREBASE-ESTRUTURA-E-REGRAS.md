# Firebase: estrutura e regras do plug-in

O plug-in usa a mesma estrutura principal do acervo. Ele não cria uma pasta separada chamada `indesign` e não grava campo `origem_upload`.

## Estrutura no Firebase Storage

```text
Firebase Storage
└── acervo-visual-unificado/
    ├── thumbnails/
    │   └── {origem}/
    │       └── {ano}/
    │           └── IMG-{ano}-{id}.jpg
    │
    └── originals/
        ├── raster/
        │   └── {origem}/
        │       └── {ano}/
        │           └── IMG-{ano}-{id}.{jpg|jpeg|png}
        │
        └── vector/
            └── {origem}/
                └── {ano}/
                    └── IMG-{ano}-{id}.{eps|ai|svg}
```

Exemplos:

```text
acervo-visual-unificado/thumbnails/shutterstock/2026/IMG-2026-a1b2c3d4.jpg
acervo-visual-unificado/originals/raster/shutterstock/2026/IMG-2026-a1b2c3d4.jpg
acervo-visual-unificado/originals/vector/envato/2026/IMG-2026-e5f6g7h8.eps
```

## Estrutura no Firestore

Coleção usada:

```text
acervo-visual-unificado/default/images
```

Campos principais gravados:

```json
{
  "uuid": "id-do-documento",
  "codigo": "id-do-documento",
  "nome_amigavel": "IMG-2026-a1b2c3d4",
  "nome_original": "imagem-original.jpg",
  "url_thumbnail": "https://firebasestorage.googleapis.com/...",
  "url_original": "https://firebasestorage.googleapis.com/...",
  "storage_thumbnail": "acervo-visual-unificado/thumbnails/origem/ano/arquivo.jpg",
  "storage_original": "acervo-visual-unificado/originals/raster/origem/ano/arquivo.jpg",
  "caminho_arquivo_original": "V:/Banco_de_Imagens/...",
  "origem": "shutterstock",
  "sha256": "hash-do-arquivo",
  "extensao": ".jpg",
  "tamanho_mb": 3.25,
  "data_processamento": "2026-08-03T15:00:00.000Z"
}
```

## Deduplicação

Antes do upload, o plug-in calcula o SHA-256 do arquivo original e consulta o Firestore.

Se já existir um documento com o mesmo `sha256`, o upload é ignorado e o contador de duplicados é atualizado.

## Regras Firebase

Os arquivos de referência ficam em:

```text
config/storage.rules
config/firestore.rules
```

Esses arquivos são modelos para o administrador aplicar no Firebase Console ou via Firebase CLI.

Resumo da regra esperada:

- leitura pública ou controlada conforme decisão do acervo;
- gravação apenas para usuários autenticados;
- permissão de escrita dentro de `acervo-visual-unificado`.
