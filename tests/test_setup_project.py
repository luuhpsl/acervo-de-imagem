"""Testes da personalização do template.

Exercitam o `setup_project.py` sobre uma cópia do projeto atual. Só fazem
sentido enquanto o projeto ainda é o template pristino: depois do setup, as
interfaces e a demonstração que eles manipulam podem já ter sido removidas —
e restaurá-las é, por decisão de projeto, tarefa do Git.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _is_pristine_template() -> bool:
    state_file = PROJECT_ROOT / ".template-state.json"
    if not state_file.exists():
        return False
    state = json.loads(state_file.read_text(encoding="utf-8"))
    return bool(state["interface"] == "both" and not state["exampleRemoved"])


pytestmark = pytest.mark.skipif(
    not _is_pristine_template(),
    reason="o projeto já foi personalizado; o setup do template não se aplica mais",
)


def _copy_fixture(destination: Path) -> None:
    for directory in ("src", "scripts", "docs", "skills"):
        shutil.copytree(PROJECT_ROOT / directory, destination / directory)
    for name in (
        ".template-state.json",
        "pyproject.toml",
        "README.md",
        "AGENTS.md",
        "CLAUDE.md",
        "tasks.md",
    ):
        shutil.copy2(PROJECT_ROOT / name, destination / name)


def test_setup_personaliza_e_produz_shell_valido(tmp_path: Path) -> None:
    _copy_fixture(tmp_path)
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(tmp_path / "scripts" / "setup_project.py"),
            "--name",
            "Meu Produto",
            "--display-name",
            "Meu Produto Desktop",
            "--description",
            'Descrição com "aspas"',
            "--organization",
            "Equipe Exemplo",
            "--remove-example",
            "--reset-tasks",
            "--no-sync-skills",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    package = tmp_path / "src" / "meu_produto"
    assert package.is_dir()
    assert not (package / "features" / "notes").exists()
    assert "features.notes" not in (package / "cli.py").read_text(encoding="utf-8")
    assert "Python Project Template" not in (package / "__init__.py").read_text(encoding="utf-8")
    assert "python-project-template" not in (tmp_path / "docs/architecture.md").read_text(
        encoding="utf-8"
    )

    metadata = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["name"] == "meu-produto"
    assert metadata["project"]["description"] == 'Descrição com "aspas"'
    assert metadata["project"]["authors"][0]["name"] == "Equipe Exemplo"

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(tmp_path / "src")
    smoke = subprocess.run(
        [sys.executable, "-c", "from meu_produto.cli import main; raise SystemExit(main([]))"],
        cwd=tmp_path,
        env=environment,
        check=False,
    )
    assert smoke.returncode == 0


def test_setup_dry_run_idempotencia_e_interface_gui(tmp_path: Path) -> None:
    _copy_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    before = pyproject.read_text(encoding="utf-8")
    dry_run = subprocess.run(
        [sys.executable, "scripts/setup_project.py", "--name", "dry-app", "--dry-run"],
        cwd=tmp_path,
        check=False,
    )
    assert dry_run.returncode == 0
    assert pyproject.read_text(encoding="utf-8") == before

    command = [
        sys.executable,
        "scripts/setup_project.py",
        "--name",
        "gui-app",
        "--display-name",
        "GUI App",
        "--interface",
        "gui",
        "--no-sync-skills",
    ]
    assert subprocess.run(command, cwd=tmp_path, check=False).returncode == 0  # noqa: S603
    first = pyproject.read_text(encoding="utf-8")
    assert subprocess.run(command, cwd=tmp_path, check=False).returncode == 0  # noqa: S603
    assert pyproject.read_text(encoding="utf-8") == first
    assert not (tmp_path / "src/gui_app/cli.py").exists()
    assert (tmp_path / "src/gui_app/gui.py").exists()
    assert "[project.scripts]" not in first
    assert "[project.gui-scripts]" in first


def test_setup_restaura_estado_em_falha_intermediaria(tmp_path: Path) -> None:
    _copy_fixture(tmp_path)
    package = tmp_path / "src/app_template/__init__.py"
    package.write_text('__version__ = "0.0.0"\n', encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    before = pyproject.read_text(encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/setup_project.py",
            "--name",
            "broken-app",
            "--display-name",
            "Broken App",
            "--no-sync-skills",
        ],
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 1
    assert pyproject.read_text(encoding="utf-8") == before
    assert package.exists()
    assert not (tmp_path / "src/broken_app").exists()
