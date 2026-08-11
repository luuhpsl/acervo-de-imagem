# Arquitetura

O projeto foi adaptado do template Python para uma aplicação desktop GUI.

## Organização

```text
src/acervo_visual_inteligente/
├── __init__.py          # versão do pacote
├── __main__.py          # entrada padrão: chama a GUI
├── gui.py               # interface Tkinter e composição visual
├── catalogo_logic.py    # lógica de processamento do acervo
├── auth_server.py       # autenticação local via Flask/Firebase
├── Icons - Programa/    # ícones e imagens da interface
├── Font/                # fontes locais
├── acervo.ico
└── index.html
```

## Decisões atuais

- A aplicação principal é GUI.
- A versão do pacote fica em `src/acervo_visual_inteligente/__init__.py`.
- Segredos não ficam versionados: use `.env.local` ou variáveis de ambiente.
- `token.json`, `credentials.json`, filas locais e logs são ignorados pelo Git.
- A fila de processamento usa checkpoint a cada 10 arquivos para reduzir risco de perda de progresso.

## Integrações

- OpenAI para análise visual e geração de metadados.
- Firebase Auth para login.
- Firebase Storage para originais e thumbnails.
- Firestore para metadados catalogados.

## Observação técnica

O código herdado ainda concentra parte da lógica em `catalogo_logic.py`. A estrutura do template já prepara o projeto para futuras separações em features, serviços e casos de uso, mas a migração foi mantida conservadora para preservar o funcionamento validado do programa.
