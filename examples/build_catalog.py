#!/usr/bin/env python3
"""Generate a 20-page representative catalog for the deck skill."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PAGE_TYPES = [
    "cover",
    "section",
    "statement",
    "cards",
    "bullets",
    "table",
    "deflist",
    "tree",
    "flow",
    "timeline",
    "bar",
    "column",
    "donut",
    "progress",
    "matrix",
    "shots",
    "compare",
    "quote",
    "stat",
    "gate",
]


def _load_deck() -> type:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "deck" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from deck import Deck

    return Deck


def _make_shot(path: Path, title: str, accent: tuple[int, int, int]) -> None:
    img = Image.new("RGB", (900, 1200), "white")
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("Arial.ttf", 54)
        font_body = ImageFont.truetype("Arial.ttf", 34)
    except OSError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    draw.rectangle((0, 0, 900, 120), fill=accent)
    draw.text((56, 38), title, fill="white", font=font_title)
    draw.rounded_rectangle((56, 190, 844, 380), radius=24, fill=(242, 244, 250))
    draw.text((96, 250), "Representative screen fixture", fill=(40, 45, 60), font=font_body)
    draw.rounded_rectangle((56, 450, 844, 820), radius=24, outline=(210, 216, 230), width=4)
    for i, width in enumerate([620, 500, 690, 430]):
        y = 510 + i * 70
        draw.rounded_rectangle((96, y, 96 + width, y + 28), radius=14, fill=accent)
    draw.rounded_rectangle((220, 960, 680, 1040), radius=40, fill=accent)
    draw.text((350, 984), "Action", fill="white", font=font_body)
    img.save(path)


def build(output: Path) -> Path:
    Deck = _load_deck()
    d = Deck(palette="indigo", footer="deck skill catalog")

    with tempfile.TemporaryDirectory(prefix="deck-shots-") as tmp:
        tmpdir = Path(tmp)
        shot_a = tmpdir / "dashboard.png"
        shot_b = tmpdir / "detail.png"
        _make_shot(shot_a, "Dashboard", (61, 82, 213))
        _make_shot(shot_b, "Detail", (123, 104, 200))

        d.cover("Deck Builder Catalog", "20 representative slide forms", "macOS stable · Windows beta")
        d.section("01", "Narrative Structure", "Slides are selected by content relationship.")
        d.statement("Pick the form before writing slide text.", "The builder is a constraint system, not a decoration layer.")
        d.cards("Operating Signals", [
            ("Forms", "20", "Representative pages"),
            ("Default", "1", "Primary builder per slide"),
            ("Fallback", "0.5x", "Bullets stay rare"),
        ])
        d.bullets("Fallback Bullets", [
            "Use when no stronger content relationship exists.",
            "Keep each item short.",
            "Split slides before shrinking below readable size.",
        ])
        d.table("Release Comparison", ["Area", "macOS", "Windows beta"], [
            ["Generate", "Verified", "Verified in Windows CI"],
            ["Polish", "Verified", "Script included; target QA pending"],
            ["Render QA", "Verified", "Adapter included; target QA pending"],
        ], col_ratio=[2, 3, 3])
        d.deflist("Format Decisions", [
            ("2-column table", "Use deflist when the left column is only a label."),
            ("Donut label", "Put the numeric value in the category label."),
            ("Fixed template", "Ask before redesigning externally mandated layouts."),
        ])
        d.tree("Skill Package", [
            ("deck/", ["SKILL.md", "scripts/", "assets/"], "Installable skill"),
            ("examples/", ["build_catalog.py"], "Smoke catalog"),
            ("agents/", ["openai.yaml"], "Codex routing metadata"),
        ])
        d.flow("Deck Workflow", [
            ("Preflight", "Check OS deps"),
            ("Classify", "New or existing"),
            ("Build", "Call one form"),
            ("Render", "Inspect PDF"),
        ], per_row=4)
        d.timeline("Validation Roadmap", [
            ("Now", "macOS preflight", True),
            ("Next", "Windows generation"),
            ("Later", "Windows render parity"),
        ])
        d.chart("Issue Volume", [("Text", 12), ("Chart", 8), ("Font", 5)], kind="bar")
        d.chart("Builder Usage", [("Cards", 9), ("Flow", 6), ("Gate", 4)], kind="column")
        d.chart("Deck Mix", [("Planning 45", 45), ("Status 35", 35), ("Sales 20", 20)], kind="donut")
        d.progress("Package Progress", [
            ("Skill docs", 100, "ready"),
            ("Examples", 100, "ready"),
            ("Windows QA", 35, "beta"),
        ])
        d.matrix("Builder Choice", "Structure", "Evidence density", [
            ("statement", 0.20, 0.25, False),
            ("cards", 0.45, 0.55, False),
            ("gate", 0.82, 0.80, True),
            ("table", 0.70, 0.45, False),
        ], quadrants=("narrative", "decision", "lightweight", "dense"))
        d.shots("Screenshot Fixtures", [str(shot_a), str(shot_b)], captions=["Dashboard", "Detail"])
        d.compare("Packaging Decision", "Duplicated OS repos", "One installable repo", [
            ("Maintenance", "Two divergent docs", "One source of truth"),
            ("Support claim", "Easier to overstate", "Beta clearly labelled"),
            ("Install", "Different paths", "Same deck/ payload"),
        ])
        d.quote("The deck should make the decision visible before it looks pretty.", "So-Yul workflow note", sub="Design principle")
        d.stat("20", "Representative page types in one catalog", notes=["Generated from the public builder API", "PPTX, PDF, and contact sheet included"])
        d.gate("Publish Gate", [
            ("README states install path", "pass", "Clone plus symlink/copy"),
            ("Windows claim scoped", "pass", "Beta only"),
            ("macOS render evidence", "pass", "PPTX and embedded-font PDF"),
            ("Windows target evidence", "wait", "Run on a physical Windows host"),
        ])

        if len(d.prs.slides) != len(PAGE_TYPES):
            raise RuntimeError(f"expected {len(PAGE_TYPES)} slides, got {len(d.prs.slides)}")

        output.parent.mkdir(parents=True, exist_ok=True)
        return Path(d.save(str(output)))


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/private/tmp/deck-builder-catalog.pptx")
    result = build(output)
    print(f"wrote {result}")
    print(f"pages {len(PAGE_TYPES)}: {', '.join(PAGE_TYPES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
