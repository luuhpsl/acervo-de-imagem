#!/usr/bin/env python3
"""Personaliza o template com dry-run, rollback e estado idempotente."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict, cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
STATE_FILE = PROJECT_ROOT / ".template-state.json"


class TemplateState(TypedDict):
    distributionName: str
    packageName: str
    displayName: str
    interface: str
    exampleRemoved: bool


DEFAULT_STATE: TemplateState = {
    "distributionName": "python-project-template",
    "packageName": "app_template",
    "displayName": "Python Project Template",
    "interface": "both",
    "exampleRemoved": False,
}
TRANSACTION_TARGETS = [
    ".template-state.json",
    "pyproject.toml",
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "docs",
    "skills",
    "src",
    "tests",
    "tasks.md",
    ".claude/skills",
    ".agents/skills",
]


def log(message: str) -> None:
    print(message)


def read_state() -> TemplateState:
    if not STATE_FILE.exists():
        return cast(TemplateState, dict(DEFAULT_STATE))
    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return cast(TemplateState, {**DEFAULT_STATE, **data})


def _ascii_slug(value: str, separator: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Z]+", separator, value.strip().lower()).strip(separator)
    if not slug:
        raise ValueError("O nome precisa conter ao menos uma letra ou número.")
    return slug


def slugify_distribution(name: str) -> str:
    return _ascii_slug(name, "-")


def slugify_package(name: str) -> str:
    package = _ascii_slug(name, "_")
    return package if package[0].isalpha() else f"app_{package}"


def validate_preconditions(state: TemplateState, requested_interface: str) -> None:
    for path in ("pyproject.toml", f"src/{state['packageName']}/__init__.py"):
        if not (PROJECT_ROOT / path).exists():
            raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    available = {
        "both": {"cli", "gui"},
        "cli": {"cli"},
        "gui": {"gui"},
    }[state["interface"]]
    requested = {
        "both": {"cli", "gui"},
        "cli": {"cli"},
        "gui": {"gui"},
    }[requested_interface]
    if not requested.issubset(available):
        raise ValueError(
            "Não é possível restaurar uma interface já removida; recupere-a pelo Git primeiro."
        )


def with_rollback(action: Callable[[], None]) -> None:
    backup_root = Path(tempfile.mkdtemp(prefix="python-setup-backup-"))
    existing: set[str] = set()
    try:
        for target in TRANSACTION_TARGETS:
            source = PROJECT_ROOT / target
            if not source.exists():
                continue
            existing.add(target)
            destination = backup_root / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        action()
    except Exception:
        for target in TRANSACTION_TARGETS:
            destination = PROJECT_ROOT / target
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()
            if target in existing:
                source = backup_root / target
                destination.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
        raise
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)


def rename_package(current_package: str, package_name: str) -> Path:
    current = PROJECT_ROOT / "src" / current_package
    destination = PROJECT_ROOT / "src" / package_name
    if current == destination:
        return current
    if destination.exists():
        raise FileExistsError(f"O pacote de destino já existe: {destination}")
    current.rename(destination)
    return destination


def iter_target_files() -> list[Path]:
    targets: list[Path] = []
    for base in ("src", "tests", "scripts"):
        targets.extend((PROJECT_ROOT / base).rglob("*.py"))
    for base in ("docs", "skills"):
        targets.extend((PROJECT_ROOT / base).rglob("*.md"))
    for name in ("pyproject.toml", "README.md", "AGENTS.md", "CLAUDE.md"):
        file = PROJECT_ROOT / name
        if file.exists():
            targets.append(file)
    return sorted(set(targets))


def replace_identifiers(
    state: TemplateState, distribution: str, package: str, display: str
) -> None:
    code_replacements = {
        state["packageName"]: package,
        state["distributionName"]: distribution,
        f"{state['packageName'].upper()}_": f"{package.upper()}_",
    }
    for file in iter_target_files():
        source = file.read_text(encoding="utf-8")
        replacements = dict(code_replacements)
        if file.suffix == ".md":
            replacements[state["displayName"]] = display
        updated = source
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != source:
            file.write_text(updated, encoding="utf-8")


def update_metadata(
    package_dir: Path,
    description: str,
    organization: str,
    display_name: str,
    license_name: str,
    repository_url: str,
) -> None:
    pyproject = PROJECT_ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    values = {
        "description": description,
        "license": license_name,
    }
    for key, value in values.items():
        if value:
            pattern = rf"(?m)^{key} = .*$"
            replacement = (
                f"license = {{ text = {json.dumps(value, ensure_ascii=False)} }}"
                if key == "license"
                else f"description = {json.dumps(value, ensure_ascii=False)}"
            )
            text = re.sub(pattern, replacement, text, count=1)
    if organization:
        text = re.sub(
            r'(?m)^authors = \[\{ name = ".*" \}\]$',
            f"authors = [{{ name = {json.dumps(organization, ensure_ascii=False)} }}]",
            text,
            count=1,
        )
    if repository_url:
        repository_line = f"Repository = {json.dumps(repository_url, ensure_ascii=False)}"
        if "[project.urls]" in text:
            text = re.sub(
                r"(?ms)^\[project\.urls\]\n.*?(?=^\[|\Z)",
                f"[project.urls]\n{repository_line}\n\n",
                text,
                count=1,
            )
        else:
            text += f"\n[project.urls]\n{repository_line}\n"
    pyproject.write_text(text, encoding="utf-8")

    init_file = package_dir / "__init__.py"
    source = init_file.read_text(encoding="utf-8")
    updated = re.sub(
        r'(?m)^APP_DISPLAY_NAME = ".*"$',
        f"APP_DISPLAY_NAME = {json.dumps(display_name, ensure_ascii=False)}",
        source,
        count=1,
    )
    if updated == source and display_name not in source:
        raise ValueError("APP_DISPLAY_NAME não encontrado no pacote.")
    init_file.write_text(updated, encoding="utf-8")


def set_project_entry_points(package_name: str, distribution: str, interface: str) -> None:
    pyproject = PROJECT_ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = re.sub(r"(?ms)\n*^\[project\.scripts\]\n.*?(?=^\[|\Z)", "\n", text)
    text = re.sub(r"(?ms)\n*^\[project\.gui-scripts\]\n.*?(?=^\[|\Z)", "\n", text)
    entries = ""
    if interface in {"cli", "both"}:
        entries += f'\n[project.scripts]\n{distribution} = "{package_name}.cli:main"\n'
    if interface in {"gui", "both"}:
        entries += f'\n[project.gui-scripts]\n{distribution}-gui = "{package_name}.gui:main"\n'
    marker = "[dependency-groups]"
    text = text.replace(marker, f"{entries}\n{marker}", 1)
    text = re.sub(r"\n{3,}", "\n\n", text)
    pyproject.write_text(text, encoding="utf-8")


def write_feature_public_api(package_name: str, interface: str) -> None:
    feature = PROJECT_ROOT / "src" / package_name / "features" / "notes"
    if not feature.exists():
        return
    imports = []
    exports = [
        "Note",
        "NoteStorageConflictError",
        "NoteStorageError",
        "NoteValidationError",
        "NotesSnapshot",
        "add_note",
        "create_note",
        "list_notes",
        "remove_note",
        "validate_title",
    ]
    if interface in {"cli", "both"}:
        imports.append(
            f"from {package_name}.features.notes.commands import register_notes_commands"
        )
        exports.append("register_notes_commands")
    if interface in {"gui", "both"}:
        imports.append(
            f"from {package_name}.features.notes.gui import NotesController, create_notes_panel"
        )
        exports.extend(["NotesController", "create_notes_panel"])
    imports.extend(
        [
            f"from {package_name}.features.notes.model import (\n"
            "    Note,\n"
            "    NoteValidationError,\n"
            "    create_note,\n"
            "    validate_title,\n"
            ")",
            f"from {package_name}.features.notes.services import (\n"
            "    NotesSnapshot,\n"
            "    NoteStorageConflictError,\n"
            "    NoteStorageError,\n"
            ")",
            f"from {package_name}.features.notes.use_cases import (\n"
            "    add_note,\n"
            "    list_notes,\n"
            "    remove_note,\n"
            ")",
        ]
    )
    source = "\n".join(imports) + "\n\n__all__ = [\n"
    source += "".join(f'    "{name}",\n' for name in sorted(exports))
    source += "]\n"
    (feature / "__init__.py").write_text(source, encoding="utf-8")


def configure_interface(package_name: str, distribution: str, interface: str) -> None:
    package = PROJECT_ROOT / "src" / package_name
    feature = package / "features" / "notes"
    if interface == "cli":
        for path in (
            package / "gui.py",
            feature / "gui.py",
            PROJECT_ROOT / "tests/test_gui.py",
            PROJECT_ROOT / "tests/features/notes/test_gui.py",
        ):
            path.unlink(missing_ok=True)
    if interface == "gui":
        for path in (
            package / "cli.py",
            feature / "commands.py",
            PROJECT_ROOT / "tests/features/notes/test_commands.py",
        ):
            path.unlink(missing_ok=True)
    write_feature_public_api(package_name, interface)
    selected_module = "gui" if interface == "gui" else "cli"
    (package / "__main__.py").write_text(
        f"from {package_name}.{selected_module} import main\n\n"
        'if __name__ == "__main__":\n    raise SystemExit(main())\n',
        encoding="utf-8",
    )
    set_project_entry_points(package_name, distribution, interface)


def write_empty_compositions(package_name: str, distribution: str, interface: str) -> None:
    package = PROJECT_ROOT / "src" / package_name
    if interface in {"cli", "both"}:
        (package / "cli.py").write_text(
            f'''import argparse
from collections.abc import Sequence
from {package_name} import APP_DISPLAY_NAME, __version__

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="{distribution}", description=APP_DISPLAY_NAME)
    parser.add_argument("--version", action="version", version=f"%(prog)s {{__version__}}")
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
''',
            encoding="utf-8",
        )
    if interface in {"gui", "both"}:
        (package / "gui.py").write_text(
            f"""from collections.abc import Callable
from typing import Protocol
from {package_name} import APP_DISPLAY_NAME
from {package_name}.logger import get_logger

logger = get_logger(__name__)

class GuiWindow(Protocol):
    def mainloop(self) -> None: ...

class GuiUnavailableError(RuntimeError):
    pass

WindowFactory = Callable[[], GuiWindow]

def build_window() -> GuiWindow:
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError as exc:
        raise GuiUnavailableError("Tkinter não está instalado neste Python.") from exc
    try:
        window = tk.Tk()
    except tk.TclError as exc:
        raise GuiUnavailableError("não foi possível acessar um ambiente gráfico.") from exc
    window.title(APP_DISPLAY_NAME)
    ttk.Label(window, text="Projeto pronto para sua primeira feature.", padding=24).pack()
    return window

def main(window_factory: WindowFactory | None = None) -> int:
    factory = build_window if window_factory is None else window_factory
    try:
        window = factory()
    except GuiUnavailableError as exc:
        logger.error(f"GUI indisponível: {{exc}}")
        return 1
    window.mainloop()
    return 0
""",
            encoding="utf-8",
        )


def remove_example(package_name: str, distribution: str, interface: str) -> None:
    for path in (
        PROJECT_ROOT / "src" / package_name / "features" / "notes",
        PROJECT_ROOT / "tests" / "features" / "notes",
    ):
        if path.exists():
            shutil.rmtree(path)
    write_empty_compositions(package_name, distribution, interface)


def reset_tasks() -> None:
    (PROJECT_ROOT / "tasks.md").write_text(
        "# Tarefas\n\nRegistre aqui as tarefas do projeto.\n\n"
        "## A fazer\n\n## Em andamento\n\n## Concluído\n",
        encoding="utf-8",
    )


def run_sync_skills() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "sync_skills.py")], cwd=PROJECT_ROOT, check=False
    )
    if result.returncode != 0:
        raise RuntimeError("A sincronização de skills falhou.")


def apply_changes(args: argparse.Namespace) -> None:
    state = read_state()
    distribution = slugify_distribution(args.name or state["distributionName"])
    package = slugify_package(distribution)
    display = args.display_name or state["displayName"]
    interface = args.interface or state["interface"]
    validate_preconditions(state, interface)
    log("\nPlano do setup:")
    log(f"  - distribuição: {state['distributionName']} -> {distribution}")
    log(f"  - pacote: {state['packageName']} -> {package}")
    log(f"  - interface: {state['interface']} -> {interface}")
    log(f"  - demonstração: {'remover' if args.remove_example else 'preservar'}")
    if args.dry_run:
        log("\nDry-run concluído; nenhum arquivo foi alterado.")
        return

    def transaction() -> None:
        package_dir = rename_package(state["packageName"], package)
        replace_identifiers(state, distribution, package, display)
        update_metadata(
            package_dir,
            args.description or "",
            args.organization or "",
            display,
            args.license or "",
            args.repository_url or "",
        )
        configure_interface(package, distribution, interface)
        if args.remove_example and not state["exampleRemoved"]:
            remove_example(package, distribution, interface)
        if args.reset_tasks or args.init_docs:
            reset_tasks()
        if not args.no_sync_skills:
            run_sync_skills()
        new_state: TemplateState = {
            "distributionName": distribution,
            "packageName": package,
            "displayName": display,
            "interface": interface,
            "exampleRemoved": state["exampleRemoved"] or args.remove_example,
        }
        STATE_FILE.write_text(
            json.dumps(new_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    with_rollback(transaction)
    log("\nSetup concluído. Rode `python scripts/dev.py validate`.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name")
    parser.add_argument("--display-name", dest="display_name")
    parser.add_argument("--description")
    parser.add_argument("--organization")
    parser.add_argument("--license")
    parser.add_argument("--repository-url", dest="repository_url")
    parser.add_argument("--interface", choices=("cli", "gui", "both"))
    parser.add_argument("--remove-example", action="store_true")
    parser.add_argument("--reset-tasks", action="store_true")
    parser.add_argument("--init-docs", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-sync-skills", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not any(vars(args).values()) and not sys.stdin.isatty():
        parser.print_help()
        return 0
    apply_changes(args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Erro durante o setup: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
