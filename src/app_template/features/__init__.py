"""Espaco das features do produto.

Cada capacidade do produto vive em sua propria pasta em `features/`, reunindo
model (logica pura), services (I/O) e commands (ligacao com a CLI). Uma feature
nunca importa arquivos internos de outra feature — apenas a interface publica
exposta pelo `__init__.py` de cada uma.
"""
