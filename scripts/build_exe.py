#!/usr/bin/env python3
"""Gera executáveis standalone para as interfaces CLI ou GUI.

Cross-platform: roda no Windows, macOS e Linux usando apenas stdlib para
orquestrar. O PyInstaller não faz cross-compilação; gere cada executável no
sistema operacional de destino.

Uso:
    python scripts/build_exe.py
    python scripts/build_exe.py --interface gui
    python scripts/build_exe.py --interface gui --name meu-app
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Interface = Literal["cli", "gui"]
ENTRY_MODULES: dict[Interface, Path] = {
    "cli": PROJECT_ROOT / "src" / "app_template" / "__main__.py",
    "gui": PROJECT_ROOT / "src" / "app_template" / "gui.py",
}
DEFAULT_NAMES: dict[Interface, str] = {
    "cli": "app-template",
    "gui": "app-template-gui",
}


def _pyinstaller_cmd(name: str, interface: Interface, entry_module: Path) -> list[str]:
    """Monta o comando do PyInstaller para a interface escolhida."""
    base = (
        ["uv", "run", "pyinstaller"]
        if shutil.which("uv")
        else [sys.executable, "-m", "PyInstaller"]
    )
    mode = ["--windowed"] if interface == "gui" else []
    return [
        *base,
        "--onefile",
        *mode,
        "--name",
        name,
        "--paths",
        str(PROJECT_ROOT / "src"),
        "--clean",
        "--noconfirm",
        str(entry_module),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera um executável standalone para a CLI ou a GUI."
    )
    parser.add_argument(
        "--interface",
        choices=("cli", "gui"),
        default="cli",
        help="Interface a empacotar (padrão: cli).",
    )
    parser.add_argument("--name", help="Nome do executável gerado.")
    args = parser.parse_args(argv)

    interface: Interface = args.interface
    entry_module = ENTRY_MODULES[interface]
    name = args.name or DEFAULT_NAMES[interface]

    if not entry_module.exists():
        print(f"Módulo de entrada não encontrado: {entry_module}", file=sys.stderr)
        return 1

    cmd = _pyinstaller_cmd(name, interface, entry_module)
    print(f"Interface: {interface}")
    print(f"Sistema: {platform.system()} ({platform.machine()})")
    print(f"$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
    if result.returncode == 0:
        suffix = ".exe" if platform.system() == "Windows" else ""
        print(f"\nExecutável gerado em: dist/{name}{suffix}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
