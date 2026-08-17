from __future__ import annotations

import argparse
from typing import Any

import pytest

from app_template.cli import main
from app_template.features.notes.commands import register_notes_commands
from app_template.features.notes.use_cases import list_notes


def test_cli_despacha_para_a_feature(
    capsys: pytest.CaptureFixture[str], isolated_data_dir: Any
) -> None:
    """A composição precisa encontrar e executar o comando registrado aqui."""
    assert main(["notes", "add", "Nota via CLI"]) == 0
    capsys.readouterr()

    assert main(["notes", "list"]) == 0
    out, _ = capsys.readouterr()
    assert "Nota via CLI" in out


def test_cli_propaga_codigo_de_erro_da_feature(
    capsys: pytest.CaptureFixture[str], isolated_data_dir: Any
) -> None:
    assert main(["notes", "add", "   "]) == 1
    _, err = capsys.readouterr()
    assert "Erro:" in err


def test_notes_add_and_list(capsys: pytest.CaptureFixture[str], isolated_data_dir: Any) -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    register_notes_commands(subparsers)

    # Add
    args_add = parser.parse_args(["notes", "add", "Minha nota CLI"])
    assert args_add.handler(args_add) == 0
    out, _ = capsys.readouterr()
    assert "adicionada com sucesso!" in out

    # List
    args_list = parser.parse_args(["notes", "list"])
    assert args_list.handler(args_list) == 0
    out, _ = capsys.readouterr()
    assert "Minha nota CLI" in out

    # Add error
    args_add_err = parser.parse_args(["notes", "add", "  "])
    assert args_add_err.handler(args_add_err) == 1
    _, err = capsys.readouterr()
    assert "obrigatório" in err


def test_notes_remove(capsys: pytest.CaptureFixture[str], isolated_data_dir: Any) -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    register_notes_commands(subparsers)

    args_add = parser.parse_args(["notes", "add", "Temp"])
    args_add.handler(args_add)
    capsys.readouterr()  # consume

    notes = list_notes()
    note_id = notes[0].id

    # Remove
    args_remove = parser.parse_args(["notes", "remove", note_id])
    assert args_remove.handler(args_remove) == 0
    out, _ = capsys.readouterr()
    assert "removida com sucesso" in out

    # Remove erro
    args_remove_err = parser.parse_args(["notes", "remove", "123"])
    assert args_remove_err.handler(args_remove_err) == 1
    _, err = capsys.readouterr()
    assert "não encontrada" in err


def test_notes_list_reporta_arquivo_corrompido(
    capsys: pytest.CaptureFixture[str], isolated_data_dir: Any
) -> None:
    (isolated_data_dir / "notes.json").write_text("{corrompido", encoding="utf-8")
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    register_notes_commands(subparsers)

    args = parser.parse_args(["notes", "list"])
    assert args.handler(args) == 1
    _, err = capsys.readouterr()
    assert "corrompido" in err
