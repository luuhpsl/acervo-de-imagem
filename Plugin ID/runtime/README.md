# Pasta runtime

Esta pasta guarda arquivos locais necessários para o plug-in funcionar na máquina de cada colaborador.

## Arquivo esperado

```text
runtime/token.json
```

Formato:

```json
{
  "token": "ID_TOKEN_FIREBASE_DO_USUARIO"
}
```

O arquivo `token.example.json` é apenas um modelo. Cada colaborador deve ter o seu próprio `token.json`.

Normalmente o `token.json` é criado automaticamente depois que o colaborador:

1. abre o plug-in no InDesign;
2. clica em `Login`;
3. autentica no navegador.

O fluxo normal de login deve ser iniciado pelo botão `Login` dentro do painel do InDesign.

Por segurança, o `token.json` real não deve ser enviado para o GitHub.
