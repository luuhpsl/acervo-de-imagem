"""Adapta a feature de notas para a linha de comando.

Erros vão para `stderr` sem carimbo de data nem nome de módulo: é o que um
terminal espera, e permite redirecionar saída útil e diagnóstico em separado.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from app_template.features.notes.services import NoteStorageError
from app_template.features.notes.use_cases import add_note, list_notes, remove_note


def _fail(message: str) -> int:
    """Reporta um erro no canal correto e devolve o código de saída."""
    print(f"Erro: {message}", file=sys.stderr)
    return 1


def _handle_add(args: argparse.Namespace) -> int:
    try:
        note = add_note(args.title)
    except (ValueError, NoteStorageError) as exc:
        return _fail(str(exc))
    print(f"Nota adicionada com sucesso! (ID: {note.id})")
    return 0


def _handle_list(_args: argparse.Namespace) -> int:
    try:
        notes = list_notes()
    except NoteStorageError as exc:
        return _fail(str(exc))
    if not notes:
        print("Nenhuma nota encontrada.")
        return 0

    print(f"{'ID':<38} | {'Título':<30} | Data")
    print("-" * 85)
    for note in notes:
        print(f"{note.id:<38} | {note.title[:30]:<30} | {note.created_at}")
    return 0


def _handle_remove(args: argparse.Namespace) -> int:
    try:
        success = remove_note(args.id)
    except NoteStorageError as exc:
        return _fail(str(exc))
    if not success:
        return _fail(f"Nota com ID {args.id} não encontrada.")
    print(f"Nota {args.id} removida com sucesso!")
    return 0


def register_notes_commands(subparsers: Any) -> None:
    notes = subparsers.add_parser("notes", help="Gerenciador de notas.")
    notes_actions = notes.add_subparsers(dest="action", metavar="<acao>")
    notes_actions.required = True

    add = notes_actions.add_parser("add", help="Adiciona uma nova nota.")
    add.add_argument("title", help="Título da nota.")
    add.set_defaults(handler=_handle_add)

    list_cmd = notes_actions.add_parser("list", help="Lista todas as notas.")
    list_cmd.set_defaults(handler=_handle_list)

    remove = notes_actions.add_parser("remove", help="Remove uma nota pelo ID.")
    remove.add_argument("id", help="ID da nota.")
    remove.set_defaults(handler=_handle_remove)
