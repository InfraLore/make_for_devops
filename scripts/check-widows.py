#!/usr/bin/env python3
"""Check PDF for widows — single lines orphaned at the top of a page.

A widow is detected when a page's first line of real content starts with a
lowercase letter, indicating it is a continuation of a paragraph from the
previous page rather than a new section heading.

Usage:
    python3 scripts/check-widows.py                    # default path
    python3 scripts/check-widows.py path/to/file.pdf
"""

import re
import subprocess
import sys
from pathlib import Path


PDFTO_TEXT = "pdftotext"
DEFAULT_PDF = "build/pdf/MakeForDevops.pdf"


def extract_pages(pdf_path):
    """Yield (page_num, text) for every page in the PDF."""
    result = subprocess.run(
        [PDFTO_TEXT, pdf_path, "-"],
        capture_output=True, text=True, check=True,
    )
    for i, page in enumerate(result.stdout.split("\f"), start=1):
        yield i, page


def content_lines(page_text):
    """Return non-empty, non-form-feed lines from the page."""
    for line in page_text.splitlines():
        line = line.strip()
        if not line or line == "\f":
            continue
        if re.match(r"^\d+$", line):
            continue
        yield line


def first_content_line(page_text):
    """Return the first real line on the page."""
    for line in content_lines(page_text):
        return line
    return ""


def show_context(page_text, max_lines=3):
    """Return the first few content lines for context display."""
    lines = list(content_lines(page_text))
    return lines[:max_lines]


def is_toc_page(page_text):
    """Heuristic: TOC pages have many lines ending with '......'."""
    lines = list(content_lines(page_text))
    toc_lines = sum(1 for l in lines if '......' in l)
    return toc_lines >= 3


def is_code_block_page(page_text):
    """Heuristic: code-heavy pages have many lines with shell prefixes."""
    lines = list(content_lines(page_text))
    code_lines = sum(1 for l in lines if l.startswith('$ ') or l.startswith('> ') or l.startswith('    '))
    return code_lines >= 5


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF

    if not Path(pdf).exists():
        print(f"PDF not found: {pdf}")
        print(f"Run 'make pdf' first, or pass the path as an argument.")
        return 1

    print(f"Checking for widows in: {pdf}\n")

    total = 0
    widows = []
    skipped_toc = 0
    skipped_code = 0

    for page_num, page_text in extract_pages(pdf):
        first = first_content_line(page_text)
        if not first:
            continue
        if not first[0].islower():
            continue

        lower = first.lower()
        if re.match(r"^\d+$", lower):
            continue
        if lower.startswith('index'):
            continue

        if is_toc_page(page_text):
            skipped_toc += 1
            continue
        if is_code_block_page(page_text):
            skipped_code += 1
            continue

        widows.append((page_num, first, show_context(page_text)))
        total += 1

    if widows:
        for page_num, first, ctx in widows:
            print(f"  Page {page_num}: {first[:100]}")
            for extra in ctx[1:3]:
                print(f"           {extra[:100]}")
            print()
        print(f"  {total} potential widow{'s' if total > 1 else ''} found.")
    else:
        print("  No widows found.")

    parts = []
    if skipped_toc:
        parts.append(f"{skipped_toc} TOC pages skipped")
    if skipped_code:
        parts.append(f"{skipped_code} code-block pages skipped")
    if parts:
        print(f"  ({'; '.join(parts)})")

    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
