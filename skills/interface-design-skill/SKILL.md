---
name: interface-design-skill
description: Use quando precisar planejar e projetar interfaces para CLI e GUI com foco na experiência do usuário (UX).
---

# Interface Design Skill

Use esta skill para orientar as melhores práticas ao projetar interfaces, sejam de linha de comando (CLI) ou gráficas (GUI).

## Diretrizes para CLI

1.  **Help Claro e Conciso:**
    *   Sempre implemente um `--help` e `-h`.
    *   Descreva brevemente o que o comando faz.
    *   Documente todos os argumentos, flags e opções.
2.  **Exit Codes (Códigos de Saída):**
    *   Retorne `0` para sucesso.
    *   Retorne diferentes de `0` para erros (ex: `1` para erros gerais, `2` para erros de uso/sintaxe da CLI).
3.  **Feedback Visual:**
    *   Use cores (de forma contida) ou símbolos para indicar sucesso, erro ou progresso.
    *   Exiba barras de progresso para tarefas demoradas.
4.  **Mensagens de Erro Acionáveis:**
    *   Ao encontrar um erro, diga o que aconteceu, por que aconteceu e (se possível) como consertar.

## Diretrizes para GUI

1.  **Framework:**
    *   Use bibliotecas robustas e portáveis (como Tkinter, PyQt ou PySide). Para o template, geralmente focamos em algo leve (como Tkinter ou CustomTkinter).
2.  **Responsividade:**
    *   A janela deve lidar bem com redimensionamentos, utilizando os gerenciadores de layout corretamente (ex: `grid` ou `pack` no Tkinter).
3.  **Feedback de UI:**
    *   Não bloqueie a thread principal (Main Thread) com operações demoradas. Use threads ou chamadas assíncronas para processamento, exibindo um indicador de carregamento.
4.  **Acessibilidade e Layout:**
    *   Agrupe controles relacionados visualmente.
    *   Mantenha espaçamento, margens e fontes legíveis.

Lembre-se: O foco é entregar uma experiência que não frustre o usuário, antecipe erros e funcione de forma intuitiva.
