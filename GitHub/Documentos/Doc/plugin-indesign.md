# Plug-in Adobe InDesign

Este documento registra a primeira etapa do plug-in UXP do Acervo de Imagens.

## Objetivo

Criar um painel dentro do Adobe InDesign para localizar imagens e links posicionados no documento ativo, permitindo que o usuário escolha manualmente quais itens serão enviados ao acervo.

Nesta fase inicial, o plug-in ainda não envia arquivos ao Firebase. A prioridade é validar a leitura dos links pelo InDesign.

## Pasta do plug-in

```text
indesign-plugin-acervo/
├── manifest.json
├── index.html
├── index.js
├── styles.css
└── README.md
```

## Fluxo da versão 0.1.0

```text
Abrir documento no InDesign
→ Abrir painel Acervo de Imagens
→ Clicar em Varrer documento
→ Plug-in lê doc.links
→ Tabela exibe arquivos encontrados
→ Usuário marca/desmarca os checkboxes
```

## Decisões do projeto

- O plug-in não cria pasta separada no Firebase.
- O plug-in não grava `origem_upload: indesign`.
- As imagens escolhidas futuramente entrarão no mesmo padrão do acervo principal.
- Links faltantes ou com erro devem aparecer no log e não devem travar o painel.

## Próxima etapa

Depois de validar a leitura dentro do InDesign, implementar:

1. cálculo de hash SHA-256;
2. verificação de duplicidade no Firestore;
3. upload dos arquivos selecionados;
4. gravação dos metadados no mesmo schema do programa desktop.
