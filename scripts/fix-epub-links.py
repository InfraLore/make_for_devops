import zipfile
import os
import re
import sys
import shutil
import tempfile

def fix_epub_crossrefs(epub_path):
    tmpdir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            z.extractall(tmpdir)

        text_dir = os.path.join(tmpdir, 'EPUB', 'text')
        if not os.path.isdir(text_dir):
            print("No EPUB/text directory found")
            return

        span_map = {}
        for fname in os.listdir(text_dir):
            if not fname.endswith('.xhtml'):
                continue
            fpath = os.path.join(text_dir, fname)
            content = open(fpath, encoding='utf-8').read()
            for m in re.finditer(r'<span id="([^"]+)"', content):
                span_map[m.group(1)] = fname

        changes = [0]
        for fname in os.listdir(text_dir):
            if not fname.endswith('.xhtml'):
                continue
            fpath = os.path.join(text_dir, fname)
            content = open(fpath, encoding='utf-8').read()

            def fix_link(m, changes=changes):
                frag = m.group(1)
                if frag in span_map and span_map[frag] != fname:
                    changes[0] += 1
                    return f'href="{span_map[frag]}#{frag}"'
                return m.group(0)

            content = re.sub(r'href="#([^"]+)"', fix_link, content)
            open(fpath, 'w', encoding='utf-8').write(content)

        os.unlink(epub_path)
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    fpath = os.path.join(root, f)
                    arcname = os.path.relpath(fpath, tmpdir)
                    z.write(fpath, arcname)

        print(f"Fixed {changes[0]} cross-references in EPUB")
    finally:
        shutil.rmtree(tmpdir)

if __name__ == '__main__':
    fix_epub_crossrefs(sys.argv[1])
