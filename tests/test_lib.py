from app_template.shared.lib import slugify


def test_slugify_normal_text() -> None:
    assert slugify("Hello World") == "hello-world"


def test_slugify_with_accents() -> None:
    assert slugify("Ação e Reação!") == "acao-e-reacao"


def test_slugify_with_multiple_spaces_and_symbols() -> None:
    assert slugify("  O que é isso?  --- ") == "o-que-e-isso"
