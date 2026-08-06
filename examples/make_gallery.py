#!/usr/bin/env python3
"""Build a catalog deck that exercises the deck skill builders."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "deck"
sys.path.insert(0, str(SKILL_DIR))
from deck import Deck  # noqa: E402


def _make_placeholder_image(path: Path, title: str, subtitle: str, fill: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1400, 900), fill)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((80, 80, 1320, 820), radius=44, outline=(255, 255, 255), width=8)
    draw.rectangle((120, 130, 470, 180), fill=(255, 255, 255))
    draw.rectangle((120, 230, 1050, 280), fill=(255, 255, 255))
    draw.rectangle((120, 330, 1180, 700), fill=(255, 255, 255))
    draw.text((150, 145), title, fill=fill)
    draw.text((150, 245), subtitle, fill=fill)
    img.save(path)


def build_gallery(out_path: Path) -> Path:
    assets_dir = ROOT / "examples" / "assets"
    img1 = assets_dir / "screen-1.png"
    img2 = assets_dir / "screen-2.png"
    img3 = assets_dir / "screen-3.png"
    _make_placeholder_image(img1, "Builder screen 1", "A simple placeholder for shots()", (61, 82, 213))
    _make_placeholder_image(img2, "Builder screen 2", "A second placeholder for shots()", (58, 111, 196))
    _make_placeholder_image(img3, "Builder screen 3", "A third placeholder for shots()", (26, 26, 26))

    d = Deck(palette="indigo", footer="Deck catalog")
    d.cover("Deck Builder Catalog", "All major slide families in one deck", "macOS stable · Windows beta")
    d.statement("Form first, bullets last.", "The builder is chosen by the content relationship.")
    d.cards(
        "Signal Cards",
        [
            ("Render", "100%", "Pretendard embedded"),
            ("Paths", "2", "macOS + Windows"),
            ("Builders", "15+", "The main families are covered"),
            ("Risk", "Beta", "Windows export parity remains bounded"),
        ],
        eyebrow="signals",
    )
    d.table(
        "Decision Matrix",
        ["Need", "Builder", "Why"],
        [
            ["Sequence", "flow()", "ordered steps"],
            ["Milestone", "timeline()", "dated roadmap"],
            ["Hierarchy", "tree()", "containment"],
            ["One number", "stat()", "single north-star"],
        ],
        col_ratio=[3, 2, 4],
    )
    d.deflist(
        "Definitions",
        [
            ("deck.py", "The fixed-theme presentation builder."),
            ("polish.py", "The cleanup pass for existing decks."),
            ("verify_pdf_fonts.py", "Checks Pretendard embedding in the rendered PDF."),
            ("deps-macos.sh", "macOS preflight and install path."),
        ],
    )
    d.tree(
        "Hierarchy",
        [
            ("Build", ["cover", "statement", "cards"], "Generation"),
            ("Shape", ["table", "deflist", "tree"], "Structure"),
            ("Visual", ["flow", "timeline", "chart"], "Data"),
        ],
    )
    d.flow(
        "Workflow",
        [("Preflight", "Check deps"), ("Build", "Generate PPTX"), ("Render", "Export PDF"), ("Verify", "Inspect fonts")],
        per_row=4,
    )
    d.timeline(
        "Roadmap",
        [("Now", "macOS stable", True), ("Next", "Windows beta", False), ("Later", "Gallery polish", False)],
    )
    d.chart("Bar Mix", [("Render", 100), ("Windows", 30), ("Gallery", 80)], kind="bar")
    d.chart("Share Mix", [("Stable 70", 70), ("Beta 30", 30)], kind="donut")
    d.progress("Progress", [("Core", 100, "done"), ("Windows", 60, "beta"), ("Gallery", 85, "local only")])
    d.matrix(
        "Positioning",
        "Automation",
        "Polish",
        [("Deck", 0.55, 0.85, True), ("Polish", 0.35, 0.75, False), ("Windows", 0.75, 0.45, False)],
        quadrants=("Low", "High", "Low", "High"),
    )
    d.shots("Screens", [str(img1), str(img2), str(img3)], captions=["PPT export", "PDF export", "Font check"])
    d.compare(
        "Before / After",
        "Before",
        "After",
        [
            ("Borders", "every box framed", "shape borders removed"),
            ("Fonts", "fallback risk", "Pretendard embedded"),
            ("Render", "manual guess", "verified PDF"),
        ],
    )
    d.quote("The real win is not making slides faster; it is making the output reproducible.", "So-Yul · deck owner", sub="Public skill repo")
    d.stat("20+", "Builders and checks covered", notes=["The catalog is intentionally broad.", "Windows stays beta until real-machine QA."])
    d.gate(
        "Release Gate",
        [
            ("Pretendard bundled", "pass", "fonts ship in repo"),
            ("macOS render path", "pass", "LibreOffice or PowerPoint"),
            ("Windows parity", "wait", "beta until real-machine render"),
        ],
    )
    d.bullets("Fallback", ["Use bullets only when no stronger shape fits.", "The catalog shows the preferred shapes first."])
    return Path(d.save(str(out_path)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "examples" / "output" / "deck-catalog.pptx"))
    args = parser.parse_args()
    out = build_gallery(Path(args.output))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
