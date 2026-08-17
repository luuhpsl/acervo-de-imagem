# Visão geral

O Acervo de Imagens é uma aplicação desktop para organizar um grande acervo visual local e preparar esses materiais para uso futuro em um banco de imagens web.

O programa foi pensado para lidar com milhares de arquivos espalhados em subpastas. Ele identifica imagens e vetores, cria uma versão leve para visualização, usa IA para preencher metadados descritivos e envia os arquivos para Firebase.

## Objetivo

Centralizar imagens e arquivos vetoriais em uma estrutura segura na nuvem, mantendo metadados suficientes para pesquisa, curadoria, download e futura publicação em site.

## Problema que resolve

Antes do sistema, os arquivos ficavam apenas no computador ou rede local, com pouca padronização de nomes, descrição, palavras-chave e controle de duplicidade. Isso dificultava encontrar imagens e aumentava o risco de perda.

Com o sistema:

- Os originais ficam no Firebase Storage.
- As thumbnails ficam separadas para carregamento rápido.
- Os metadados ficam no Firestore.
- Arquivos com falha podem ser reprocessados.
- Processamentos longos podem ser retomados com fila/checkpoint.

## Tipos de arquivo suportados

- JPG
- JPEG
- PNG
- EPS
- AI
- SVG

Arquivos vetoriais são convertidos temporariamente para JPG para análise e thumbnail, mas o original vetorial também é enviado para download futuro.

## Integrações

- OpenAI: análise visual e geração de metadados.
- Firebase Authentication: login.
- Firebase Storage: armazenamento de originais e thumbnails.
- Firestore: armazenamento dos metadados.
- ImageMagick/Ghostscript: conversão de EPS/AI/SVG.

## Estado atual

Versão atual documentada: `2.0.11`.

Principais recursos recentes:

- Vitrine compatível com a coleção principal e com o caminho legado do Firestore.
- Normalização dos metadados novos para pesquisa, visualização e exportação.
- Descrições acessíveis mais completas geradas para pessoas com deficiência visual.
- Log com cores distintas para mensagens normais, sucessos, avisos e erros.
- Substituição de imagens semelhantes com remoção baseada nos caminhos reais do Storage.
- Layout retrô novo.
- Tema escuro/claro.
- Checkpoint de fila.
- Reprocessamento de pendências.
- Botão de upload para carregar JSON de retomada.
- Preferência por imagem colorida quando houver versão PB e colorida.
- Barra de rolagem customizada acompanhando o tema.
