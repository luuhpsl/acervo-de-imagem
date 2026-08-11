# Instalação para colaboradores

Este plug-in deve ser distribuído com a pasta inteira `Plugin ID`.

Não copie apenas arquivos soltos. Para funcionar corretamente, mantenha esta estrutura:

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

## Requisitos

- Adobe InDesign compatível com UXP.
- UXP Developer Tool instalado.
- Usuário autorizado no Firebase.
- Python instalado na máquina para rodar o servidor local de login.

## Como carregar o plug-in

1. Abra o Adobe InDesign.
2. Abra o UXP Developer Tool.
3. Clique em `Add Plugin` ou `Load Plugin`.
4. Selecione o arquivo:

```text
Plugin ID/manifest.json
```

5. Clique em `Load`.
6. No InDesign, abra o painel do plug-in em `Plugins > Acervo de Imagens`.

## Login e token

O botão de login do painel abre o navegador padrão do Windows para autenticação Microsoft/Google.

Observação: o arquivo `ABRIR_LOGIN_PLUGIN.url` sozinho só funciona se o servidor local já estiver ativo. Para abrir manualmente o fluxo completo, use `ABRIR_LOGIN_NAVEGADOR.vbs`.

Na primeira execução, o InDesign pode exibir uma autorização para abrir o processo externo. O usuário deve permitir, pois essa autorização é necessária para o botão `Login` abrir o navegador.

O token gerado é salvo automaticamente em:

```text
Plugin ID/runtime/token.json
```

Formato esperado:

```json
{
  "token": "ID_TOKEN_FIREBASE_DO_USUARIO"
}
```

O uso normal deve ser sempre pelo botão `Login` do painel. O usuário não precisa abrir nenhum arquivo manualmente.

## Fluxo de uso

1. Abrir um documento `.indd`.
2. Fazer login no painel.
3. Clicar em `Varrer documento`.
4. Aguardar a geração das miniaturas.
5. Selecionar apenas as imagens desejadas.
6. Clicar em `Enviar selecionados`.

O plug-in ignora links fora dos formatos aceitos pelo acervo, como QR Code e outros vínculos internos.

## Formatos aceitos

- `.jpg`
- `.jpeg`
- `.png`
- `.eps`
- `.ai`
- `.svg`

## Observação importante

O arquivo real `runtime/token.json` não deve ser enviado para GitHub, e não deve ser compartilhado entre usuários.
