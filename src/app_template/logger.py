"""Logger da aplicação para diagnóstico.

Serve a mensagens de diagnóstico — não à comunicação com o usuário. A CLI
escreve erros diretamente em `stderr` (ver `features/<nome>/commands.py`),
porque carimbo de data e nome de módulo poluem a saída de um terminal. O
logger é o canal adequado onde não existe terminal, como na GUI empacotada
em modo windowed.

O nível padrão é `INFO` e pode ser ajustado sem alterar código pela variável
de ambiente `APP_TEMPLATE_LOG_LEVEL` (ex.: `DEBUG`, `WARNING`).
"""

from __future__ import annotations

import logging
import os

_ENV_LOG_LEVEL = "APP_TEMPLATE_LOG_LEVEL"
_DEFAULT_LEVEL = logging.INFO


def _configured_level() -> int:
    """Lê o nível do ambiente, caindo para INFO quando ausente ou inválido."""
    name = os.environ.get(_ENV_LOG_LEVEL, "").strip().upper()
    if not name:
        return _DEFAULT_LEVEL
    level = logging.getLevelNamesMapping().get(name)
    return level if level is not None else _DEFAULT_LEVEL


def get_logger(name: str) -> logging.Logger:
    """Devolve um logger configurado uma única vez por nome."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(_configured_level())
    return logger
