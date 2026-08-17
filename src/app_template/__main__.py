"""Permite executar o pacote com `python -m app_template`.

Delega para a mesma funcao usada pelo comando de console (`app-template`),
definido em `pyproject.toml` -> [project.scripts].
"""

from app_template.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
