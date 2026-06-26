#!/usr/bin/env python3
"""Verify required fonts are installed; download Merriweather if missing.

Reads font requirements from metadata.yml and checks each is available
via fontconfig. Merriweather is downloaded from Google Fonts if absent.
"""

import os
import re
import subprocess
import sys
import urllib.request

FONT_DIR = os.path.expanduser("~/.fonts")
METADATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.yml")

REQUIRED = [
    ("Merriweather", "mainfont"),
    ("DejaVu Sans Mono", "monofont"),
    ("Lato", "sansfont"),
]

MERRIWEATHER_CSS = (
    "https://fonts.googleapis.com/css2?"
    "family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,300;1,400;1,700;1,900"
)
WEIGHT_MAP = {
    "300": "Light",
    "400": "Regular",
    "700": "Bold",
    "900": "Black",
}
SUFFIX_MAP = {
    ("Light", True): "LightItalic",
    ("Regular", True): "Italic",
    ("Bold", True): "BoldItalic",
    ("Black", True): "BlackItalic",
}


def read_metadata_fonts():
    """Return set of font names mentioned in metadata.yml."""
    fonts = set()
    try:
        with open(METADATA) as f:
            for line in f:
                m = re.match(r"(mainfont|monofont|sansfont):\s*(.+)", line)
                if m:
                    fonts.add(m.group(2).strip())
    except FileNotFoundError:
        pass
    return fonts


def check_font(family):
    """Return True if font family is found by fontconfig."""
    result = subprocess.run(
        ["fc-list", "--format=%{family}\n", family],
        capture_output=True, text=True
    )
    families = [l.strip() for l in result.stdout.split("\n") if l.strip()]
    for entry in families:
        if family in entry.split(","):
            return True
    return False


def get_font_blocks():
    req = urllib.request.Request(
        MERRIWEATHER_CSS, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        css = resp.read().decode("utf-8")

    blocks = re.findall(r"@font-face\s*\{[^}]+\}", css)
    if not blocks:
        print("Error: Could not parse @font-face blocks from Google Fonts CSS")
        sys.exit(1)

    entries = []
    for block in blocks:
        style = re.search(r"font-style:\s*(\w+)", block)
        weight = re.search(r"font-weight:\s*(\d+)", block)
        url = re.search(r"url\(([^)]+)\)", block)
        if style and weight and url:
            entries.append((style.group(1), weight.group(1), url.group(1)))
    return entries


def download_merriweather():
    print("Downloading Merriweather from Google Fonts...")
    entries = get_font_blocks()

    os.makedirs(FONT_DIR, exist_ok=True)
    downloaded = []
    for style, weight, url in entries:
        is_italic = style == "italic"
        weight_name = WEIGHT_MAP.get(weight, weight)
        filename = f"Merriweather-{SUFFIX_MAP.get((weight_name, is_italic), weight_name)}.ttf"
        dest = os.path.join(FONT_DIR, filename)

        if os.path.exists(dest):
            continue

        print(f"  {filename}...")
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(dest, "wb") as f:
                    f.write(resp.read())
            downloaded.append(filename)
        except Exception as e:
            print(f"  Failed: {e}")

    if downloaded:
        subprocess.run(["fc-cache", "-f", FONT_DIR], capture_output=True)
        print(f"  Downloaded {len(downloaded)} file(s)")
    else:
        print("  All variants already present")


def main():
    metadata_fonts = read_metadata_fonts()
    if metadata_fonts:
        print("Fonts required by metadata.yml:")
        for f in sorted(metadata_fonts):
            print(f"  {f}")
        print()

    status = {}
    for font, label in REQUIRED:
        status[font] = check_font(font)

    missing = [f for f, ok in status.items() if not ok]

    if "Merriweather" in missing:
        print("Merriweather not found. Installing...")
        download_merriweather()
        status["Merriweather"] = check_font("Merriweather")
        missing = [f for f, ok in status.items() if not ok]

    print()
    print("Font status:")
    all_ok = True
    for font, label in REQUIRED:
        ok = status[font]
        mark = "\u2714" if ok else "\u2718"
        print(f"  {mark} {font} ({label})")
        if not ok:
            all_ok = False

    if missing:
        print(f"\nMissing: {', '.join(missing)}")
        print("Install system fonts via your package manager, e.g.:")
        print("  sudo apt install fonts-dejavu-core fonts-lato")
        sys.exit(1)
    else:
        print("\nAll required fonts are available.")


if __name__ == "__main__":
    main()
