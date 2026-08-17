"""Comportamentos dos metadados e da proteção contra duplicidade."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import ModuleType


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_SRC = REPOSITORY_ROOT / "Programa Acervo de Imagens" / "src"
if str(APPLICATION_SRC) not in sys.path:
    sys.path.insert(0, str(APPLICATION_SRC))

from acervo_visual_inteligente.gui import load_catalogo_logic  # noqa: E402


class CatalogoMetadataTests(unittest.TestCase):
    """Valida as regras observáveis sem abrir a janela Tkinter."""

    logic: ModuleType

    @classmethod
    def setUpClass(cls) -> None:
        cls.logic = load_catalogo_logic()
        cls.logic.log = lambda _message: None

    def test_visual_types_are_restricted_and_illustration_maps_to_vector(self) -> None:
        self.assertEqual(self.logic.normalizar_tipo_visual("Ilustração"), "vetorial")
        self.assertEqual(self.logic.normalizar_tipo_visual("Gráfico de dados"), "infografico")
        self.assertEqual(self.logic.normalizar_tipo_visual("Cena 3D"), "")

    def test_colors_use_portuguese_palette_without_inventing_five(self) -> None:
        colors = self.logic.normalizar_cores_metadados(
            {"colors": ["azul", "blue", "branco", "ciano", "turquesa"]}
        )
        self.assertEqual(colors, ["azul", "branco"])

    def test_shared_words_and_translations_are_kept_only_once(self) -> None:
        raw = [
            "educacao",
            "professora",
            "estudantes",
            "quadro-branco",
            "cadernos",
            "mesas",
            "aprendizagem",
            "ambiente-escolar",
            "software",
            "tecnologia",
            "software",
            "classroom",
            "teacher",
            "lesson",
            "teamwork",
            "school-supplies",
            "study-group",
        ]
        keywords = self.logic.normalizar_keywords_metadados(raw, 15)
        self.assertEqual(len(keywords), 15)
        self.assertEqual(keywords.count("software"), 1)
        self.assertNotIn("teacher", keywords)

    def test_invalid_duplicate_keywords_block_metadata(self) -> None:
        metadata = {
            "knowledge_area": "ciencias-humanas",
            "visual_type": "fotografia",
            "colors": ["azul", "branco", "cinza"],
            "description": "Fotografia de uma sala de aula com estudantes e uma professora.",
            "keywords": [
                "vetor",
                "educacao",
                "professora",
                "estudantes",
                "quadro",
                "caderno",
                "mesa",
                "aprendizagem",
                "escola",
                "aula",
                "vector",
                "teacher",
                "classroom",
                "lesson",
                "teamwork",
            ],
        }
        self.assertIsNone(self.logic.validar_metadados_ia(metadata))
        self.assertIn("15 conceitos unicos", self.logic.ultimo_erro_openai)

    def test_fewer_than_five_colors_are_valid_for_simple_images(self) -> None:
        metadata = {
            "knowledge_area": "linguagens",
            "visual_type": "vetorial",
            "colors": ["preto", "branco"],
            "description": "Vetorial de um símbolo preto centralizado sobre fundo branco.",
            "keywords": [
                "simbolo",
                "contraste",
                "forma",
                "contorno",
                "composicao",
                "centralizado",
                "monocromatico",
                "fundo-branco",
                "elemento-isolado",
                "design",
                "icon",
                "outline",
                "minimal",
                "shape",
                "contrast",
            ],
        }
        result = self.logic.validar_metadados_ia(metadata)
        self.assertIsNotNone(result)
        self.assertEqual(result["colors"], ["preto", "branco"])

    def test_uuid_is_stable_for_same_sha256(self) -> None:
        first = self.logic.gerar_uuid_deterministico("abc123")
        self.assertEqual(first, self.logic.gerar_uuid_deterministico("abc123"))
        self.assertNotEqual(first, self.logic.gerar_uuid_deterministico("outro-hash"))

    def test_firestore_listing_follows_every_page(self) -> None:
        class Response:
            status_code = 200

            def __init__(self, body: dict[str, object]) -> None:
                self._body = body

            def json(self) -> dict[str, object]:
                return self._body

        responses = iter(
            [
                Response({"documents": [{"name": "primeiro"}], "nextPageToken": "pagina-2"}),
                Response({"documents": [{"name": "segundo"}]}),
            ]
        )
        original_get = self.logic.requests.get
        self.logic.token_usuario = "token-de-teste"
        self.logic.requests.get = lambda *args, **kwargs: next(responses)
        try:
            ok, documents = self.logic.listar_documentos_firestore()
        finally:
            self.logic.requests.get = original_get

        self.assertTrue(ok)
        self.assertEqual(
            [document["name"] for document in documents],
            ["primeiro", "segundo"],
        )

    def test_only_official_firebase_paths_remain(self) -> None:
        app = REPOSITORY_ROOT / "Programa Acervo de Imagens"
        combined = "\n".join(
            (app / name).read_text(encoding="utf-8")
            for name in ("firestore.rules", "storage.rules", "index.html")
        )
        self.assertNotIn("default/images", combined)
        self.assertNotIn("originals/raster", combined)
        self.assertNotIn("thumbnails/{source}", combined)
        self.assertIn("match /acervo-visual-unificado/{imageId}", combined)

    def test_new_payload_does_not_persist_numbering_key(self) -> None:
        source = (
            REPOSITORY_ROOT / "Programa Acervo de Imagens" / "catalogo_logic.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"chave_numeracao":', source)


if __name__ == "__main__":
    unittest.main()
