---
name: plan-app
description: Conduzir pessoas não desenvolvedoras da ideia inicial até uma definição completa e aprovada do produto, por meio de perguntas curtas e decisões explícitas; usar ao iniciar um aplicativo Python com CLI, GUI, ambas, automação ou utilitário, redefinir um produto ainda vago ou antes de planejar features, para criar ou atualizar docs/prd.md e registrar as decisões correspondentes em docs/architecture.md sem implementar código.
---

# Planejar aplicativo

## Objetivo

Transformar uma ideia de produto em decisões verificáveis, compreensíveis por uma pessoa não desenvolvedora. Entrevistar o usuário até não restar nenhuma decisão necessária em aberto; somente então escrever o PRD e atualizar a arquitetura.

## Regras de conversa

1. Ler `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/building.md` e documentos de produto existentes antes de perguntar.
2. Descobrir no repositório tudo que puder ser verificado sem o usuário. Não perguntar sobre versão do Python, estrutura ou outra informação já registrada.
3. Usar linguagem cotidiana. Ao precisar de uma decisão técnica com efeito no produto, explicar primeiro o efeito em custo, prazo, risco, distribuição ou experiência.
4. Fazer de uma a três perguntas curtas e relacionadas por rodada. Priorizar a decisão que desbloqueia mais respostas.
5. Oferecer duas ou três opções concretas quando isso facilitar a resposta, indicar uma recomendação e explicar o principal trade-off. Permitir que o usuário proponha outra opção.
6. Não aceitar palavras como “simples”, “rápido”, “intuitivo”, “moderno”, “completo”, “seguro”, “depois” ou “etc.” como especificação. Pedir exemplo, limite, referência ou resultado observável.
7. Não inventar requisitos. Registrar cada ideia como `decidida`, `pendente` ou `fora do escopo` e manter esse resumo consistente entre as rodadas.
8. Se uma nova resposta contrariar uma decisão anterior, mostrar o conflito em linguagem simples e pedir qual decisão deve prevalecer.
9. Não escrever o PRD, alterar a arquitetura nem implementar código enquanto houver decisão obrigatória pendente.

## Sequência de descoberta

Avançar pela sequência de acordo com as respostas, sem transformar a conversa em um questionário rígido:

1. Definir o problema, quem o enfrenta hoje e qual resultado justificará o produto.
2. Escolher o usuário principal, os usuários secundários e quem explicitamente não será atendido na primeira versão.
3. Descrever a jornada principal passo a passo, do gatilho inicial ao resultado concluído.
4. Definir as capacidades indispensáveis da primeira versão e classificar todas as demais como fora do escopo.
5. Especificar, para cada capacidade, entradas, resultado, regras, exceções e permissões.
6. Escolher a interface do produto: CLI, GUI ou ambas; definir como a pessoa inicia, navega, fornece dados e recebe retorno.
7. Definir dados necessários, formatos de arquivo, origem, armazenamento, atualização, exclusão e informações sensíveis.
8. Definir integrações externas, dependências, falhas esperadas e comportamento sem conexão quando relevante.
9. Definir sistemas operacionais atendidos e forma de entrega: pacote Python, executável standalone ou outra opção compatível com o template.
10. Definir estados observáveis por interface: ajuda, saída e códigos de retorno na CLI; carregamento, vazio, sucesso, erro e ações indisponíveis na GUI.
11. Definir acessibilidade, teclado, redimensionamento, idioma, prazo, orçamento, desempenho e portabilidade aplicáveis.
12. Definir critérios de sucesso mensuráveis e critérios de aceite observáveis.
13. Consolidar escopo e não escopo sem itens implícitos.

Não perguntar sobre categorias que comprovadamente não se aplicam. Registrar “não se aplica” com o motivo em vez de deixar a categoria vaga.

## Teste de concretude

Considerar uma decisão concreta somente quando outra pessoa puder implementá-la e verificar o resultado sem adivinhar:

- nomear quem realiza a ação;
- informar o comando, gatilho ou entrada;
- descrever a saída e o resultado visível;
- definir regras, limites e exceções relevantes;
- cobrir entrada inválida, ausência de dados, falha e permissão quando aplicável;
- indicar como comprovar que o comportamento está correto;
- classificar claramente o item dentro ou fora da primeira versão.

Converter pedidos subjetivos em critérios observáveis. Por exemplo, trocar “o processamento deve ser rápido” por um tempo acordado para um volume definido, ou registrar que não há meta de desempenho específica para a primeira versão.

## Portão de conclusão

Antes de criar arquivos, confirmar que existem decisões explícitas para:

- problema, proposta de valor e usuário principal;
- jornada principal completa;
- escopo exato da primeira versão;
- não escopo explícito;
- requisitos funcionais e regras de negócio;
- interface ou interfaces de uso, entradas, saídas, feedback e navegação;
- dados, formatos, integrações, permissões e privacidade aplicáveis;
- sistemas operacionais, distribuição e restrições relevantes;
- critérios de sucesso e de aceite;
- compatibilidade ou conflito resolvido com os limites do template;
- zero decisões obrigatórias em aberto.

Apresentar ao usuário um resumo final com `Produto`, `Escopo`, `Não escopo`, `Decisões de arquitetura` e `Critérios de aceite`. Pedir aprovação explícita. Se houver correção, voltar à descoberta; se houver aprovação, produzir os documentos.

## Produção dos documentos

### `docs/prd.md`

Usar [assets/prd-template.md](assets/prd-template.md) como estrutura mínima. Criar o arquivo se ele não existir; se existir, atualizar somente após comparar as decisões atuais com o conteúdo anterior.

Ao preencher:

- escrever para leitores não técnicos;
- usar identificadores estáveis (`RF-01`, `RN-01`, `CA-01`);
- tornar cada requisito e critério testável;
- remover todas as instruções e marcações do modelo;
- não usar `TBD`, “a definir”, “entre outros” ou equivalentes;
- escrever `Nenhuma` em decisões em aberto;
- colocar ideias futuras no não escopo, sem tratá-las como compromisso.

### `docs/architecture.md`

Preservar as regras arquiteturais do template e atualizar somente o que as decisões aprovadas afetarem. Criar ou atualizar uma seção `Decisões do produto` contendo:

- limite do sistema, interface de uso e sistemas operacionais atendidos;
- mapa das capacidades para features;
- responsabilidades de `model.py`, `services.py`, `use_cases.py`, adaptadores `commands.py`/`gui.py` e interfaces públicas;
- fluxo dos dados, formatos de entrada e saída;
- persistência e integrações externas;
- empacotamento e forma de distribuição de cada interface;
- estratégia para manter callbacks GUI responsivos quando houver trabalho demorado;
- decisões transversais de acesso, privacidade e operação;
- restrições, trade-offs e motivos das escolhas.

Não copiar todo o PRD para a arquitetura. Não inventar tecnologia que não foi determinada pelo repositório ou aprovada. Verificar primeiro se a biblioteca padrão resolve. Se o produto exigir algo proibido pelo template, resolver o conflito com o usuário antes de concluir e registrar a decisão conforme as regras do projeto.

## Encerramento

Revisar os dois arquivos em conjunto e confirmar que não se contradizem. Informar:

- decisões consolidadas;
- arquivos criados ou alterados;
- confirmação de que não restaram pendências;
- próximo passo recomendado: usar `plan-feature` para decompor a primeira capacidade aprovada.

Não implementar o aplicativo nesta skill.
