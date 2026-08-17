# Uso

Este documento descreve o uso básico do programa.

## Abrir o programa

Com o ambiente instalado:

```powershell
acervo-visual-gui
```

Ou:

```powershell
python -m acervo_visual_inteligente.gui
```

## Login

Ao abrir, faça login com uma conta autorizada pelo Firebase. O programa usa token local para evitar login repetido.

Se precisar sair, clique em `Sair`.

## Selecionar pasta

Clique em `Selecionar Pasta` e escolha a pasta raiz do acervo.

O programa faz varredura recursiva, ou seja, também lê subpastas.

Após a varredura, o log informa:

- quantidade de arquivos encontrados;
- tamanho total em KB, MB, GB ou TB;
- arquivos ignorados por duplicidade/variação.

## Iniciar processamento

Clique no botão `Play`.

Durante o processamento, acompanhe:

- progresso;
- tempo;
- log;
- encontrados;
- processados;
- duplicados;
- erros.

Antes de enviar um arquivo, o programa verifica SHA-256 e semelhança visual no
Firestore. Se essa consulta falhar, o upload é bloqueado e o arquivo permanece
nas pendências. Isso evita cadastrar imagens sem uma verificação confiável de
duplicidade.

## Pausar

O botão `Pause` solicita pausa, mas a pausa só acontece entre uma imagem e outra. Se uma imagem já está sendo enviada/analisada, ela termina primeiro.

## Parar

O botão `Parar` interrompe o fluxo antes da próxima imagem e limpa a fila atual. Use com cuidado.

## Reprocessar pendentes

O botão `Reprocessar Pendentes` usa automaticamente o JSON de pendências salvo pelo programa.

Use quando:

- a OpenAI falhou;
- o upload falhou;
- a conversão falhou;
- houve erro de metadados.

## Upload/carregar JSON

O último botão da barra usa ícone de upload.

Ele serve para carregar manualmente um arquivo `.json` de retomada. É útil quando:

- a pessoa fechou o aviso de retomada sem querer;
- o processamento foi interrompido;
- o JSON foi levado para outra máquina;
- é necessário reconstruir uma fila manualmente.

O programa lê caminhos em formatos como:

- `files`;
- `arquivos`;
- `materiais`;
- lista simples;
- itens com campo `caminho`, `path` ou `arquivo`.

Arquivos que não existirem no computador são ignorados e informados no log.

## Exportar Excel

O botão de download exporta dados para Excel quando a função estiver configurada.

## Abrir vitrine

O botão do globo abre a vitrine/local preview.

## Tema claro/escuro

Use o seletor no canto inferior direito para alternar tema.
