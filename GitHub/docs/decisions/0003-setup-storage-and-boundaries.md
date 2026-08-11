# 0003 - Setup verificável, persistência segura e fronteiras executáveis

- **Status**: Aceito
- **Data**: 2026-07-26

## Contexto

O setup podia remover as features demonstrativas sem atualizar CLI e GUI. As regras de importação existiam apenas em documentação, e erros de persistência podiam ser registrados sem impedir mensagens de sucesso.

## Decisão

- Manter `notes` como única demonstração canônica e remover a skill de front-end web deste template.
- Separar nome exibido, distribuição, comando e pacote importável durante o setup.
- Gerar composições CLI e GUI válidas quando `--remove-example` for usado.
- Testar o setup em uma cópia temporária e importar o pacote resultante.
- Validar registros persistidos, escrever por arquivo temporário e propagar `NoteStorageError`.
- Executar `check-architecture` na validação local.
- Usar `src/app_template/__init__.py` como fonte única da versão do pacote.

## Consequências

O template fica mais previsível para pessoas e agentes, mantém zero dependências de runtime e acrescenta apenas verificações locais rápidas. Projetos personalizados deixam de carregar orientação visual específica de sites.
