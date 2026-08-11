#!/usr/bin/env python3
"""Gera o esqueleto arquitetural de uma feature sem alterar a composição."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")
    if not slug:
        raise ValueError("Informe um nome de feature válido.")
    return slug if slug[0].isalpha() else f"feature_{slug}"


def _class_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("_"))


def _package_name(root: Path) -> str:
    state = json.loads((root / ".template-state.json").read_text(encoding="utf-8"))
    return str(state["packageName"])


def _available_interfaces(root: Path) -> set[str]:
    state = json.loads((root / ".template-state.json").read_text(encoding="utf-8"))
    return {"both": {"cli", "gui"}, "cli": {"cli"}, "gui": {"gui"}}[state["interface"]]


def generate_feature(root: Path, raw_name: str, interface: str | None, dry_run: bool) -> list[Path]:
    name = _slug(raw_name)
    class_name = _class_name(name)
    package = _package_name(root)
    available = _available_interfaces(root)
    selected = (
        available
        if interface is None
        else {
            "both": {"cli", "gui"},
            "cli": {"cli"},
            "gui": {"gui"},
        }[interface]
    )
    if not selected.issubset(available):
        raise ValueError("A interface solicitada não está disponível neste projeto.")

    feature = root / "src" / package / "features" / name
    if feature.exists():
        raise FileExistsError(f'A feature "{name}" já existe.')

    exports = []
    public_names = [f'    "{class_name}Repository",', f'    "{class_name}State",']
    if "cli" in selected:
        exports.append(
            f"from {package}.features.{name}.commands import (\n    register_{name}_commands,\n)"
        )
        public_names.append(f'    "register_{name}_commands",')
    if "gui" in selected:
        exports.append(f"from {package}.features.{name}.gui import (\n    create_{name}_panel,\n)")
        public_names.append(f'    "create_{name}_panel",')
    exports.extend(
        [
            f"from {package}.features.{name}.model import (\n"
            f"    {class_name}State,\n"
            "    create_initial_state,\n"
            ")",
            f"from {package}.features.{name}.services import (\n    {class_name}Repository,\n)",
            f"from {package}.features.{name}.use_cases import (\n    load_{name}_state,\n)",
        ]
    )
    public_names.extend(['    "create_initial_state",', f'    "load_{name}_state",'])

    files = {
        "__init__.py": "\n".join(sorted(exports))
        + "\n\n__all__ = [\n"
        + "\n".join(sorted(public_names))
        + "\n]\n",
        "model.py": (
            "from __future__ import annotations\n\n"
            "from dataclasses import dataclass\n\n\n"
            "@dataclass(frozen=True, slots=True)\n"
            f"class {class_name}State:\n"
            "    name: str\n\n\n"
            f"def create_initial_state() -> {class_name}State:\n"
            f'    return {class_name}State(name="{name}")\n'
        ),
        "services.py": (
            "from __future__ import annotations\n\n"
            "from typing import Protocol\n\n"
            f"from {package}.features.{name}.model import (\n"
            f"    {class_name}State,\n"
            ")\n\n\n"
            f"class {class_name}Repository(Protocol):\n"
            f"    def load(self) -> {class_name}State:\n"
            "        ...\n"
        ),
        "use_cases.py": (
            "from __future__ import annotations\n\n"
            f"from {package}.features.{name}.model import (\n"
            f"    {class_name}State,\n"
            ")\n"
            f"from {package}.features.{name}.services import (\n"
            f"    {class_name}Repository,\n"
            ")\n\n\n"
            f"def load_{name}_state(\n"
            f"    repository: {class_name}Repository,\n"
            f") -> {class_name}State:\n"
            "    return repository.load()\n"
        ),
    }
    if "cli" in selected:
        files["commands.py"] = (
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n\n"
            f"def register_{name}_commands(subparsers: Any) -> None:\n"
            f'    subparsers.add_parser("{name.replace("_", "-")}", help="Feature {name}.")\n'
        )
    if "gui" in selected:
        files["gui.py"] = (
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    import tkinter as tk\n"
            "    from tkinter import ttk\n\n\n"
            f"def create_{name}_panel(parent: tk.Misc) -> ttk.Frame:\n"
            "    from tkinter import ttk\n\n"
            "    panel = ttk.Frame(parent, padding=16)\n"
            f'    ttk.Label(panel, text="{class_name}").pack()\n'
            "    return panel\n"
        )

    test_feature = root / "tests" / "features" / name
    test_content = (
        f"from {package}.features.{name}.model import (\n"
        "    create_initial_state,\n"
        ")\n\n\n"
        "def test_cria_estado_inicial() -> None:\n"
        f'    assert create_initial_state().name == "{name}"\n'
    )
    planned = [feature / path for path in sorted(files)] + [test_feature / "test_model.py"]
    if dry_run:
        return planned

    temporary = Path(tempfile.mkdtemp(prefix=f"{name}-", dir=feature.parent))
    try:
        for relative, content in files.items():
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
        temporary.rename(feature)
        test_feature.mkdir(parents=True)
        (test_feature / "test_model.py").write_text(test_content, encoding="utf-8")
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        shutil.rmtree(feature, ignore_errors=True)
        shutil.rmtree(test_feature, ignore_errors=True)
        raise
    return planned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--interface", choices=("cli", "gui", "both"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    files = generate_feature(args.root.resolve(), args.name, args.interface, args.dry_run)
    action = "Arquivos planejados" if args.dry_run else "Feature criada"
    print(f"{action}:")
    for file in files:
        print(f"  - {file.relative_to(args.root.resolve()).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
