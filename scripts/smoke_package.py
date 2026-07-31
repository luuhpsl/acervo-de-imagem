#!/usr/bin/env python3
"""Instala o wheel recém-gerado em ambiente limpo e verifica suas entradas."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
import venv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def smoke_package(root: Path = PROJECT_ROOT) -> None:
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    package_path = metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"][0]
    package_name = Path(package_path).name
    wheels = sorted((root / "dist").glob("*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        raise FileNotFoundError("Nenhum wheel foi encontrado em dist/.")
    state = json.loads((root / ".template-state.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="python-wheel-smoke-") as directory:
        environment = Path(directory) / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        executable = environment / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        subprocess.run(
            [str(executable), "-m", "pip", "install", "--no-index", "--no-deps", str(wheels[-1])],
            check=True,
            cwd=root,
        )
        subprocess.run(
            [str(executable), "-c", f"import {package_name}; print({package_name}.__version__)"],
            check=True,
            cwd=root,
        )
        if state["interface"] in {"cli", "both"}:
            subprocess.run([str(executable), "-m", package_name, "--help"], check=True, cwd=root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    smoke_package(args.root.resolve())
    print("Smoke test do wheel OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
