# Plug-in InDesign — Acervo de Imagens

Plug-in UXP para Adobe InDesign usado para localizar imagens vinculadas em documentos `.indd`, permitir seleção visual por miniaturas e enviar os arquivos escolhidos para o Firebase Storage/Firestore do Acervo de Imagens.

Versão atual: `v0.2.0`.

## O que o plug-in faz

- Abre um painel dentro do Adobe InDesign.
- Lê os links do documento ativo.
- Filtra apenas os formatos usados pelo acervo:
  - `.jpg`
  - `.jpeg`
  - `.png`
  - `.eps`
  - `.ai`
  - `.svg`
- Ignora links como QR Code e formatos fora do escopo.
- Gera miniaturas leves antes de exibir a lista.
- Permite escolher manualmente quais imagens serão enviadas.
- Calcula SHA-256 para evitar duplicados.
- Envia original e thumbnail para Firebase Storage.
- Grava os metadados no Firestore.
- Mantém a mesma estrutura principal do acervo, sem criar origem separada para InDesign.

## Estrutura da pasta

```text
Plugin ID/
├── manifest.json
├── auth_server_plugin.py
├── ABRIR_LOGIN_NAVEGADOR.vbs
├── ABRIR_LOGIN_PLUGIN.url
├── index.html
├── index.js
├── styles.css
├── README.md
├── config/
│   ├── acervo.config.json
│   ├── firebase.config.json
│   ├── firestore.rules
│   └── storage.rules
├── docs/
│   ├── FIREBASE-ESTRUTURA-E-REGRAS.md
│   └── INSTALACAO-COLABORADORES.md
└── runtime/
    ├── README.md
    ├── token.example.json
    └── token.json
```

## Arquivos importantes

- `manifest.json`: cadastro do plug-in para o UXP/InDesign.
- `auth_server_plugin.py`: servidor local de autenticação do plug-in.
- `ABRIR_LOGIN_NAVEGADOR.vbs`: inicia o servidor local e abre o navegador.
- `ABRIR_LOGIN_PLUGIN.url`: apenas aponta para o endereço local do login; só funciona se o servidor já estiver ativo.
- `index.html`: estrutura visual do painel.
- `styles.css`: tema escuro/claro, tabela, botões, barra de progresso e miniaturas.
- `index.js`: leitura do documento, geração de miniaturas, seleção, hash, deduplicação e upload.
- `config/firebase.config.json`: referência das configurações do Firebase.
- `config/acervo.config.json`: formatos aceitos e estrutura lógica do acervo.
- `config/storage.rules`: modelo de regra do Firebase Storage.
- `config/firestore.rules`: modelo de regra do Firestore.
- `runtime/token.json`: token local do colaborador para envio ao Firebase.
- `runtime/openai.config.json`: chave local da OpenAI usada para preencher os metadados de IA antes do envio.

## OpenAI / metadados de IA

Para enviar imagens pelo plug-in, os metadados de IA precisam ser gerados antes do upload. Crie o arquivo abaixo copiando o exemplo `runtime/openai.config.example.json`:

```text
runtime/openai.config.json
```

Conteudo esperado:

```json
{
  "openai_api_key": "SUA_CHAVE_OPENAI"
}
```

Se esse arquivo nao existir, ou se a analise da IA falhar, o plug-in nao envia o arquivo ao Firebase. Isso evita registros incompletos no Firestore.

## Instalação

Veja:

```text
docs/INSTALACAO-COLABORADORES.md
```

## Firebase

Veja:

```text
docs/FIREBASE-ESTRUTURA-E-REGRAS.md
```

## Login pelo navegador

O login do plug-in acontece pelo navegador padrão do Windows, acionado pelo botão `Login` do painel.

Fluxo:

1. O colaborador clica em `Login` no painel do InDesign.
2. O plug-in inicia o servidor local de login automaticamente.
3. O servidor abre o navegador padrão do Windows na tela de login Microsoft/Google.
4. Após autenticar, o token é salvo em:

```text
runtime/token.json
```

Esse arquivo é individual por colaborador e não deve ser enviado para GitHub.

O uso normal deve ser sempre pelo botão `Login` do painel. O usuário não precisa abrir nenhum arquivo manualmente.

Na primeira execução, o InDesign pode pedir permissão para abrir o processo externo de login. Essa permissão precisa ser aceita para que o navegador seja aberto pelo botão.
