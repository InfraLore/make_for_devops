import yaml
import sys
from pathlib import Path
from string import Template

REPO_DIR = Path(__file__).resolve().parent.parent
METADATA_FILE = REPO_DIR / "metadata.yml"
TEMPLATE_FILE = REPO_DIR / "templates" / "landing-page.html"
OUTPUT_FILE = REPO_DIR / "pages" / "index.html"


def format_creators(creator_list):
    parts = []
    for c in creator_list:
        parts.append(f"{c['role']}: {c['text']}")
    return " &middot;\n      ".join(parts)


def main():
    with open(METADATA_FILE) as f:
        docs = list(yaml.safe_load_all(f))
        meta = docs[0] if docs else {}

    with open(TEMPLATE_FILE) as f:
        template = Template(f.read())

    title = meta.get("title", "Make for DevOps")
    author = meta.get("author", "")
    rights = meta.get("rights", "CC0 1.0 Universal")
    creators = format_creators(meta.get("creator", []))

    html = template.substitute(
        title=title,
        author=author,
        rights=rights,
        creators=creators,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)

    print(f"Generated {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
