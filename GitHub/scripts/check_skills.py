#!/usr/bin/env python3
"""Verifica a integridade das skills e se as copias geradas estao sincronizadas.

Executado dentro de `python scripts/dev.py validate`. Sai com codigo != 0 em erro.
Uso: `python scripts/dev.py check-skills` (ou `python scripts/check_skills.py`).

Regras verificadas:
 1. Cada skill em `skills/` possui um `SKILL.md`.
 2. O frontmatter YAML tem `name` e `description` nao vazios.
 3. O `name` do frontmatter bate com o nome da pasta.
 4. As copias em `.claude/skills` e `.agents/skills` existem e sao identicas
    (mesmo conjunto de arquivos e conteudo byte a byte).

Cross-platform (Windows, macOS, Linux): usa apenas a stdlib.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / "skills"
DESTINATIONS = [
    PROJECT_ROOT / ".claude" / "skills",
    PROJECT_ROOT / ".agents" / "skills",
]

errors: list[str] = []


def list_skill_dirs(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    return sorted(entry.name for entry in directory.iterdir() if entry.is_dir())


def list_files_recursive(directory: Path) -> list[str]:
    """Lista caminhos de arquivo relativos a `directory`, com "/" normalizado."""
    if not directory.exists():
        return []
    files = [p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()]
    return sorted(files)


def parse_frontmatter(content: str) -> dict[str, str] | None:
    """Parser minimo de frontmatter YAML (pares `chave: valor` entre `---`)."""
    lines = content.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None

    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end == -1:
        return None

    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        idx = line.find(":")
        if idx == -1:
            continue
        key = line[:idx].strip()
        value = line[idx + 1 :].strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key:
            data[key] = value
    return data


def validate_metadata(skill: str) -> None:
    skill_md = SOURCE_DIR / skill / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f'Skill "{skill}": arquivo SKILL.md ausente.')
        return

    meta = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if meta is None:
        errors.append(
            f'Skill "{skill}": frontmatter YAML ausente ou malformado em SKILL.md '
            '(esperado bloco entre linhas "---").'
        )
        return

    name = meta.get("name")
    if not name:
        errors.append(f'Skill "{skill}": campo "name" ausente ou vazio no frontmatter.')
    elif name != skill:
        errors.append(
            f'Skill "{skill}": campo "name" ("{name}") difere do nome da pasta ("{skill}").'
        )

    if not meta.get("description"):
        errors.append(f'Skill "{skill}": campo "description" ausente ou vazio no frontmatter.')


def compare_copies(skills: list[str]) -> None:
    source_files_by_skill = {skill: list_files_recursive(SOURCE_DIR / skill) for skill in skills}

    for dest_root in DESTINATIONS:
        if not dest_root.exists():
            errors.append(
                f'Copia ausente: "{dest_root}" nao existe. '
                'Rode "python scripts/dev.py sync-skills".'
            )
            continue

        dest_skills = list_skill_dirs(dest_root)
        missing = [s for s in skills if s not in dest_skills]
        extra = [s for s in dest_skills if s not in skills]
        if missing:
            errors.append(f'"{dest_root}": skill(s) faltando: {", ".join(missing)}.')
        if extra:
            errors.append(f'"{dest_root}": skill(s) extra(s): {", ".join(extra)}.')

        for skill in skills:
            src_files = source_files_by_skill.get(skill, [])
            dest_files = list_files_recursive(dest_root / skill)
            src_set, dest_set = set(src_files), set(dest_files)

            for file in src_files:
                if file not in dest_set:
                    errors.append(f'"{dest_root}/{skill}": arquivo faltando na copia: {file}.')
                    continue
                src_bytes = (SOURCE_DIR / skill / file).read_bytes()
                dest_bytes = (dest_root / skill / file).read_bytes()
                if src_bytes != dest_bytes:
                    errors.append(f'"{dest_root}/{skill}": conteudo divergente em {file}.')

            for file in dest_files:
                if file not in src_set:
                    errors.append(f'"{dest_root}/{skill}": arquivo extra na copia: {file}.')


def main() -> int:
    skills = list_skill_dirs(SOURCE_DIR)
    if not skills:
        print(f'Nenhuma skill encontrada em "{SOURCE_DIR}".', file=sys.stderr)
        return 1

    for skill in skills:
        validate_metadata(skill)
    compare_copies(skills)

    if errors:
        print("Verificacao de skills FALHOU:\n", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            f'\nTotal de problemas: {len(errors)}. Rode "python scripts/dev.py sync-skills".',
            file=sys.stderr,
        )
        return 1

    print(f"Verificacao de skills OK: {len(skills)} skill(s) validada(s) e sincronizada(s).")
    for skill in skills:
        print(f"  - {skill}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
