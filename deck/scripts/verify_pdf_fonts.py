#!/usr/bin/env python3
"""Verify that a rendered PDF still carries the intended font family.

Usage:
  python3 verify_pdf_fonts.py input.pptx output.pdf
  python3 verify_pdf_fonts.py --allow-missing-pdffonts input.pptx output.pdf
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - exercised only in missing optional dep envs
    PdfReader = None


def _pptx_uses_pretendard(pptx_path: Path) -> bool:
    if not pptx_path.exists():
        raise FileNotFoundError(f"missing PPTX: {pptx_path}")
    with zipfile.ZipFile(pptx_path) as zf:
        for name in zf.namelist():
            if not name.startswith("ppt/slides/slide") or not name.endswith(".xml"):
                continue
            text = zf.read(name).decode("utf-8", errors="ignore")
            if "Pretendard" in text:
                return True
    return False


def _pdffonts_report(pdf_path: Path) -> str | None:
    pdffonts = shutil.which("pdffonts")
    if not pdffonts:
        return None
    proc = subprocess.run([pdffonts, str(pdf_path)], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "pdffonts failed")
    return proc.stdout


def _contains(report: str, pattern: str) -> bool:
    return re.search(pattern, report, flags=re.IGNORECASE) is not None


def _resolve(obj):
    try:
        return obj.get_object()
    except Exception:
        return obj


def _font_row(font) -> set[str]:
    names: set[str] = set()
    descriptors = []

    for key in ("/BaseFont", "/Name"):
        value = font.get(key)
        if value:
            names.add(str(value).lstrip("/"))

    descriptor = _resolve(font.get("/FontDescriptor", {}))
    if descriptor:
        descriptors.append(descriptor)

    descendants = _resolve(font.get("/DescendantFonts", [])) or []
    for descendant_ref in descendants:
        descendant = _resolve(descendant_ref)
        for key in ("/BaseFont", "/Name"):
            value = descendant.get(key)
            if value:
                names.add(str(value).lstrip("/"))
        child_descriptor = _resolve(descendant.get("/FontDescriptor", {}))
        if child_descriptor:
            descriptors.append(child_descriptor)

    for item in descriptors:
        for key in ("/FontName", "/BaseFont"):
            value = item.get(key)
            if value:
                names.add(str(value).lstrip("/"))

    embedded = any(
        any(key in item for key in ("/FontFile", "/FontFile2", "/FontFile3"))
        for item in descriptors
    )
    rows = set()
    for name in names:
        cleaned = re.sub(r"^[A-Z]{6}\+", "", name).replace(" ", "")
        rows.add(f"{cleaned} emb={'yes' if embedded else 'no'}")
    return rows


def _resource_font_rows(resources, seen: set[int]) -> set[str]:
    resources = _resolve(resources or {})
    if not resources or id(resources) in seen:
        return set()
    seen.add(id(resources))

    rows: set[str] = set()
    fonts = _resolve(resources.get("/Font", {})) or {}
    for ref in fonts.values():
        rows.update(_font_row(_resolve(ref)))

    xobjects = _resolve(resources.get("/XObject", {})) or {}
    for ref in xobjects.values():
        xobject = _resolve(ref)
        rows.update(_resource_font_rows(xobject.get("/Resources", {}), seen))
    return rows


def _pypdf_report(pdf_path: Path) -> str | None:
    if PdfReader is None:
        return None
    reader = PdfReader(str(pdf_path))
    rows: set[str] = set()
    seen: set[int] = set()
    for page in reader.pages:
        rows.update(_resource_font_rows(page.get("/Resources", {}), seen))
    return "\n".join(sorted(rows))


def _pretendard_embedded(report: str) -> bool:
    lines = [line for line in report.splitlines() if re.search(r"Pretendard", line, re.IGNORECASE)]
    if not lines:
        return False
    for line in lines:
        if re.search(r"\bemb=yes\b", line, re.IGNORECASE):
            continue
        parts = line.split()
        if len(parts) >= 5 and parts[-5].lower() == "yes":
            continue
        return False
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-missing-pdffonts", action="store_true")
    parser.add_argument("pptx")
    parser.add_argument("pdf")
    args = parser.parse_args(argv)

    pptx_path = Path(args.pptx)
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"missing PDF: {pdf_path}")

    if not _pptx_uses_pretendard(pptx_path):
        print("SKIP: PPTX does not reference Pretendard")
        return 0

    report = _pdffonts_report(pdf_path)
    if report is None:
        report = _pypdf_report(pdf_path)
    if report is None:
        message = "SKIP: no PDF font inspection backend is available"
        if args.allow_missing_pdffonts:
            print(message)
            return 0
        print(message, file=sys.stderr)
        return 1

    if not _contains(report, r"Pretendard"):
        print("FAIL: Pretendard is missing from the PDF font table", file=sys.stderr)
        return 1

    if not _pretendard_embedded(report):
        print("FAIL: Pretendard is present but not embedded in the PDF", file=sys.stderr)
        return 1

    if _contains(report, r"Arial\s*Narrow|ArialNarrow|STHeiti"):
        print("FAIL: fallback font detected in PDF font table", file=sys.stderr)
        return 1

    print("PASS: Pretendard is embedded and no narrow fallback font was detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
