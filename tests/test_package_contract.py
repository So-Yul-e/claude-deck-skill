from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "deck"


class PackageContractTests(unittest.TestCase):
    def test_required_public_package_files_exist(self) -> None:
        required = [
            REPO / "README.md",
            REPO / "README.ko.md",
            REPO / "LICENSE",
            REPO / "THIRD_PARTY_NOTICES.md",
            SKILL / "SKILL.md",
            SKILL / "agents" / "openai.yaml",
            SKILL / "scripts" / "deck.py",
            SKILL / "scripts" / "polish.py",
            SKILL / "scripts" / "deps-macos.sh",
            SKILL / "scripts" / "render-macos.sh",
            SKILL / "scripts" / "deps-windows.ps1",
            SKILL / "scripts" / "render-windows.ps1",
            SKILL / "assets" / "fonts" / "Pretendard-Regular.otf",
            SKILL / "assets" / "fonts" / "Pretendard-Bold.otf",
            SKILL / "assets" / "fonts" / "OFL.txt",
            REPO / "examples" / "build_catalog.py",
        ]
        missing = [str(path.relative_to(REPO)) for path in required if not path.is_file()]
        self.assertEqual([], missing)

    def test_skill_metadata_contract(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill_text.startswith("---\n"))
        self.assertRegex(skill_text, r"(?m)^name:\s*deck\s*$")
        self.assertNotIn("TO" + "DO", skill_text)

        openai_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$deck", openai_yaml)

    def test_readme_language_switch_and_catalog_claims(self) -> None:
        english = (REPO / "README.md").read_text(encoding="utf-8")
        korean = (REPO / "README.ko.md").read_text(encoding="utf-8")

        self.assertIn('href="README.ko.md"', english)
        self.assertIn('href="README.md"', korean)
        self.assertIn("20 representative slide types", english)
        self.assertIn("대표 슬라이드 20종", korean)

    def test_catalog_covers_twenty_render_types(self) -> None:
        source = (REPO / "examples" / "build_catalog.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls: list[tuple[str, str | None]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            method = node.func.attr
            if method != "chart":
                calls.append((method, None))
                continue
            kind = None
            for keyword in node.keywords:
                if keyword.arg == "kind" and isinstance(keyword.value, ast.Constant):
                    kind = str(keyword.value.value)
            calls.append((method, kind))

        expected = {
            ("cover", None),
            ("section", None),
            ("statement", None),
            ("cards", None),
            ("bullets", None),
            ("table", None),
            ("deflist", None),
            ("tree", None),
            ("flow", None),
            ("timeline", None),
            ("chart", "bar"),
            ("chart", "column"),
            ("chart", "donut"),
            ("progress", None),
            ("matrix", None),
            ("shots", None),
            ("compare", None),
            ("quote", None),
            ("stat", None),
            ("gate", None),
        }
        self.assertTrue(expected.issubset(set(calls)), expected.difference(calls))

    def test_font_license_boundary_is_preserved(self) -> None:
        notice = (REPO / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        ofl = (SKILL / "assets" / "fonts" / "OFL.txt").read_text(encoding="utf-8")

        self.assertIn("not covered by this project's\nMIT license", notice)
        self.assertIn("Copyright (c) 2021, Kil Hyung-jin", ofl)
        self.assertIn("Reserved Font Name 'Pretendard'", ofl)
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", ofl)

    def test_no_private_paths_or_secret_assignments(self) -> None:
        text_suffixes = {".md", ".py", ".sh", ".ps1", ".yaml", ".yml", ".txt"}
        forbidden = [
            re.compile("/Users/" + "so-yul", re.IGNORECASE),
            re.compile(r"(?:api[_-]?key|token|password)\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE),
        ]
        hits: list[str] = []
        for path in REPO.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in text_suffixes:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in forbidden:
                if pattern.search(text):
                    hits.append(str(path.relative_to(REPO)))
        self.assertEqual([], sorted(set(hits)))


if __name__ == "__main__":
    unittest.main()
