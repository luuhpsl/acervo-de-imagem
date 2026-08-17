#!/usr/bin/env python3
"""Verifica as fronteiras arquiteturais do código em ``src``."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _package_name(root: Path) -> str:
    packages = sorted(path.name for path in (root / "src").iterdir() if path.is_dir())
    if len(packages) != 1:
        raise ValueError("Esperado exatamente um pacote dentro de src/.")
    return packages[0]


def _target_feature(module: str, package_name: str) -> tuple[str | None, bool]:
    parts = module.split(".")
    prefix = [package_name, "features"]
    if parts[:2] != prefix or len(parts) < 3:
        return None, False
    return parts[2], len(parts) == 3


def _resolve_import_from(node: ast.ImportFrom, relative: Path) -> str | None:
    if node.module is None:
        return None
    if node.level == 0:
        return node.module

    current_package = list(relative.parent.parts)
    parent_hops = node.level - 1
    if parent_hops > len(current_package):
        return node.module
    base = current_package[: len(current_package) - parent_hops]
    return ".".join([*base, *node.module.split(".")])


def check_architecture(root: Path = PROJECT_ROOT) -> list[str]:
    source_root = root / "src"
    package_name = _package_name(root)
    errors: list[str] = []

    for file in source_root.rglob("*.py"):
        relative = file.relative_to(source_root)
        parts = relative.parts
        source_feature = parts[2] if len(parts) > 2 and parts[1] == "features" else None
        source_is_shared = len(parts) > 1 and parts[1] == "shared"
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))

        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                resolved = _resolve_import_from(node, relative)
                if resolved:
                    modules.append(resolved)
            else:
                continue

            for module in modules:
                target_feature, is_public = _target_feature(module, package_name)
                if source_is_shared and target_feature:
                    errors.append(
                        f"{relative.as_posix()}:{node.lineno}: shared não pode importar "
                        f'a feature "{target_feature}".'
                    )
                elif target_feature and target_feature != source_feature and not is_public:
                    errors.append(
                        f"{relative.as_posix()}:{node.lineno}: importe a feature "
                        f'"{target_feature}" apenas por seu __init__.py.'
                    )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    errors = check_architecture(args.root.resolve())
    if errors:
        print("Verificação arquitetural FALHOU:\n")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Verificação arquitetural OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
