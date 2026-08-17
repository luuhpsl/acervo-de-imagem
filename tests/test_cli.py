"""Testes da composição da CLI.

Cobrem apenas o contrato que sobrevive à personalização: ajuda, versão e
entrada do módulo. O despacho para uma feature é testado junto da própria
feature (ex.: `tests/features/notes/test_commands.py`), porque o setup pode
remover a demonstração.
"""

from __future__ import annotations

import importlib

import pytest

from app_template import APP_DISPLAY_NAME, __version__
from app_template.cli import build_parser, main


def test_sem_comando_mostra_ajuda_e_sai_com_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    out, _ = capsys.readouterr()
    assert "usage:" in out
    assert APP_DISPLAY_NAME in out


def test_version_reporta_a_versao_do_pacote(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    out, _ = capsys.readouterr()
    assert __version__ in out


def test_parser_identifica_a_aplicacao() -> None:
    parser = build_parser()

    assert parser.description == APP_DISPLAY_NAME


def test_argumento_desconhecido_falha_com_codigo_de_uso() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--inexistente"])

    assert exit_info.value.code == 2


def test_modulo_de_execucao_reexporta_a_entrada() -> None:
    """`python -m app_template` precisa continuar apontando para a CLI."""
    module = importlib.import_module("app_template.__main__")

    assert module.main is main
