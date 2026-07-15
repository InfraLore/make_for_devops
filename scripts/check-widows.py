#!/usr/bin/env python3
"""Check PDF for widows — single lines orphaned at the top of a page.

A widow is detected when a page's first line of real content starts with a
lowercase letter, indicating it is a continuation of a paragraph from the
previous page rather than a new recipe/section title.

Pages that look like data tables or index entries are excluded automatically
since they are common false positives.  All other lowercase-starting pages
are flagged with surrounding context so a human can review.

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
        # Skip bare page numbers (standalone digits)
        if re.match(r"^\d+$", line):
            continue
        yield line


def first_content_line(page_text):
    """Return the first real line on the page."""
    for line in content_lines(page_text):
        return line
    return ""


def lines_starting_with(prefix, lines):
    """Count how many *lines* start with *prefix* (for data-table detection)."""
    return sum(1 for l in lines if l.startswith(prefix))


def looks_like_data_table(page_text):
    """Heuristic: scaling / reference tables have short rows with numbers.

    A data-table page typically has a single-word header followed by
    rows that begin with a quantity or unit pattern like "1x", "1/2 C",
    "1 1/2x", etc.
    """
    lines = list(content_lines(page_text))
    if len(lines) < 3:
        return False
    # Check if second line starts with a number followed by "x" (scaling factor)
    if len(lines) > 1:
        second = lines[1]
        if re.match(r"^\d+", second) and re.search(r"x$", second, re.IGNORECASE):
            return True
    # Check if many lines start with a quantity pattern like "1/2 C", "3 T", etc.
    data_rows = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\d+\s+\w", stripped):
            data_rows += 1
    if data_rows >= 3:
        return True
    return False


def looks_like_index(page_text):
    """Heuristic: index pages have many lines ending in a page number."""
    lines = list(content_lines(page_text))
    if len(lines) < 3:
        return False
    # Count lines that contain a page reference pattern:  "Word, NNN" or
    # "Multi Word, NNN" where NNN is a number.
    entry_count = 0
    for line in lines:
        # Index entries: text followed by comma, space, and a number
        if re.search(r",\s*\d+$", line):
            entry_count += 1
    # If at least half the lines look like index entries, it's an index page
    return entry_count >= len(lines) // 2


def show_context(page_text, max_lines=3):
    """Return the first few content lines for context display."""
    lines = list(content_lines(page_text))
    return lines[:max_lines]


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF

    if not Path(pdf).exists():
        print(f"❌ PDF not found: {pdf}")
        print(f"   Run 'make pdf' first, or pass the path as an argument.")
        return 1

    print(f"Checking for widows in: {pdf}\n")

    total = 0
    widows = []
    skipped_table = 0
    skipped_index = 0
    skipped_pattern = 0

    for page_num, page_text in extract_pages(pdf):
        first = first_content_line(page_text)
        if not first:
            continue
        if not first[0].islower():
            continue

        # -- pattern-based skip --
        lower = first.lower()
        if re.match(r"^\d+$", lower):
            continue  # bare page number
        if re.match(r"^[a-z]+(/[a-z]+)? \.\.\.", lower):
            continue  # TOC continuation line
        if lower.startswith("index"):
            skipped_pattern += 1
            continue  # index page header by itself

        # -- content-based skip --
        if looks_like_data_table(page_text):
            skipped_table += 1
            continue
        if looks_like_index(page_text):
            skipped_index += 1
            continue

        # -- looks like a real widow --
        widows.append((page_num, first, show_context(page_text)))
        total += 1

    if widows:
        for page_num, first, ctx in widows:
            print(f"  ⚠ Page {page_num}: {first[:100]}")
            for extra in ctx[1:3]:
                print(f"           {extra[:100]}")
            print()
        print(f"  {total} potential widow{'s' if total > 1 else ''} found.")
    else:
        print("  ✅ No widows found.")

    # Report skip statistics
    parts = []
    if skipped_table:
        parts.append(f"{skipped_table} table pages skipped")
    if skipped_index:
        parts.append(f"{skipped_index} index pages skipped")
    if skipped_pattern:
        parts.append(f"{skipped_pattern} pattern-skipped pages")
    if parts:
        print(f"  ({'; '.join(parts)})")

    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
