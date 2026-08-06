from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "deck" / "scripts" / "verify_pdf_fonts.py"
SPEC = importlib.util.spec_from_file_location("deck_verify_pdf_fonts", MODULE_PATH)
assert SPEC and SPEC.loader
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class PdfVerifierTests(unittest.TestCase):
    def test_committed_catalog_uses_and_embeds_pretendard(self) -> None:
        pptx = REPO / "examples" / "output" / "deck-builder-catalog.pptx"
        pdf = REPO / "examples" / "output" / "deck-builder-catalog.pdf"

        self.assertTrue(VERIFY._pptx_uses_pretendard(pptx))
        report = VERIFY._pypdf_report(pdf)
        self.assertIsNotNone(report)
        self.assertIn("Pretendard", report)
        self.assertTrue(VERIFY._pretendard_embedded(report))
        self.assertNotRegex(report, r"Arial\s*Narrow|ArialNarrow|STHeiti")

    def test_embedding_parser_fails_closed(self) -> None:
        self.assertTrue(VERIFY._pretendard_embedded("Pretendard-Regular emb=yes"))
        self.assertFalse(VERIFY._pretendard_embedded("Pretendard-Regular emb=no"))
        self.assertFalse(VERIFY._pretendard_embedded("NanumGothic emb=yes"))


if __name__ == "__main__":
    unittest.main()
