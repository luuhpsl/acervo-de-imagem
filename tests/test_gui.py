"""Testes do ponto de entrada GUI sem abrir uma janela real."""

from __future__ import annotations

import pytest

from app_template.gui import GuiUnavailableError, main


class FakeWindow:
    """Janela mínima para observar a execução do loop de eventos."""

    def __init__(self) -> None:
        self.started = False

    def mainloop(self) -> None:
        self.started = True


def test_main_executa_loop_da_gui() -> None:
    window = FakeWindow()

    assert main(lambda: window) == 0
    assert window.started is True


def test_main_explica_quando_gui_nao_esta_disponivel(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def unavailable() -> FakeWindow:
        raise GuiUnavailableError("sem display")

    assert main(unavailable) == 1
    assert "GUI indisponível: sem display" in caplog.text
