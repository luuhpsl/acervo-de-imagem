"""Testes do logger de diagnóstico."""

from __future__ import annotations

import logging

import pytest

from app_template.logger import get_logger


def test_reaproveita_o_mesmo_logger_sem_duplicar_handlers() -> None:
    """Chamar duas vezes não pode fazer cada mensagem aparecer em dobro."""
    first = get_logger("app_template.testes.reuso")
    second = get_logger("app_template.testes.reuso")

    assert first is second
    assert len(first.handlers) == 1


def test_usa_info_como_nivel_padrao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_TEMPLATE_LOG_LEVEL", raising=False)

    assert get_logger("app_template.testes.padrao").level == logging.INFO


def test_respeita_o_nivel_configurado_no_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_TEMPLATE_LOG_LEVEL", "debug")

    assert get_logger("app_template.testes.ambiente").level == logging.DEBUG


def test_ignora_nivel_invalido_em_vez_de_quebrar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Uma variável mal preenchida não pode impedir a aplicação de subir."""
    monkeypatch.setenv("APP_TEMPLATE_LOG_LEVEL", "não-é-um-nível")

    assert get_logger("app_template.testes.invalido").level == logging.INFO
