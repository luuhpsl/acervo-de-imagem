#!/usr/bin/env python3
"""Sincroniza as skills canonicas de `skills/` para as copias geradas.

As copias vivem em `.claude/skills` e `.agents/skills`. NAO edite as copias
manualmente: elas sao recriadas por este script.

Uso: `python scripts/dev.py sync-skills` (ou `python scripts/sync_skills.py`).

Cross-platform (Windows, macOS, Linux): usa apenas a stdlib (pathlib, shutil).
"""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / "skills"
DESTINATIONS = [
    PROJECT_ROOT / ".claude" / "skills",
    PROJECT_ROOT / ".agents" / "skills",
]


def list_skill_dirs(directory: Path) -> list[str]:
    """Lista as pastas de skill (arquivos soltos na raiz sao ignorados)."""
    if not directory.exists():
        return []
    return sorted(entry.name for entry in directory.iterdir() if entry.is_dir())


def sync_skills() -> None:
    skills = list_skill_dirs(SOURCE_DIR)
    if not skills:
        print(f'Nenhuma skill encontrada em "{SOURCE_DIR}". Nada a sincronizar.')
        return

    for dest_root in DESTINATIONS:
        # Remove a pasta antiga inteira e recria do zero.
        if dest_root.exists():
            shutil.rmtree(dest_root)
        dest_root.mkdir(parents=True, exist_ok=True)

        for skill in skills:
            shutil.copytree(SOURCE_DIR / skill, dest_root / skill)

        print(f'Sincronizadas {len(skills)} skill(s) para "{dest_root}":')
        for skill in skills:
            print(f"  - {skill}")

    print("\nSincronizacao concluida com sucesso.")


if __name__ == "__main__":
    sync_skills()
