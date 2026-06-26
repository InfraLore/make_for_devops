"""Convert straight quotes to curly quotes and `---` to em dashes in chapter
prose, while preserving headings, code blocks, LaTeX commands, and URLs."""

import os
import re
import sys


def is_prose_line(line, in_code_block):
    stripped = line.strip()
    if not stripped:
        return False
    if in_code_block:
        return False
    if stripped.startswith('#'):
        return False
    if stripped.startswith('\\'):
        return False
    if stripped.startswith('|') or stripped.startswith('\\rowcolor'):
        return False
    if stripped.startswith('```'):
        return False
    if stripped.startswith('http') or stripped.startswith('from http'):
        return False
    if stripped == '---':
        return False
    return True


def smart_quotes(text):
    result = []
    in_double = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == '\\' and i + 1 < len(text) and text[i + 1] in '{}\\_':
            result.append(c)
            i += 1
            continue
        if c == '"':
            if i > 0 and text[i - 1].isdigit():
                result.append(c)
            else:
                if not in_double:
                    result.append('\u201c')
                    in_double = True
                else:
                    result.append('\u201d')
                    in_double = False
            i += 1
            continue
        if c == "'":
            if i > 0 and i + 1 < len(text):
                prev_char = text[i - 1]
                next_char = text[i + 1]
                if prev_char.isalpha() and next_char.isalpha():
                    result.append('\u2019')
                elif prev_char.isalpha() and next_char in 'sS ':
                    result.append('\u2019')
                elif prev_char in ' ([' and next_char.isalpha():
                    result.append('\u2018')
                elif prev_char in ',.!?;:' and next_char in ' )':
                    result.append('\u2019')
                else:
                    result.append('\u2019')
            else:
                result.append('\u2019')
            i += 1
            continue
        result.append(c)
        i += 1
    return ''.join(result)


def fix_dashes(text):
    text = re.sub(r'(?<!\n)---(?!\n)', ' \u2014 ', text)
    text = re.sub(r'(?<=[a-zA-Z])--(?=[a-zA-Z])', ' \u2014 ', text)
    return text


def process_file(fpath, check_only=False):
    with open(fpath, encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
        if is_prose_line(line, in_code_block):
            new_line = fix_dashes(line)
            new_line = smart_quotes(new_line)
            if new_line != line:
                modified = True
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    if modified and not check_only:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return modified


def main():
    check_only = '--check' in sys.argv
    chapters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chapters')
    parts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parts')

    changed = []
    for directory in (chapters_dir, parts_dir):
        for fname in sorted(os.listdir(directory)):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(directory, fname)
            if process_file(fpath, check_only):
                changed.append(os.path.join(os.path.basename(directory), fname))

    if changed:
        print(f"{'Would modify' if check_only else 'Modified'} {len(changed)} files:")
        for f in changed:
            print(f"  {f}")
        if check_only:
            sys.exit(1)
    else:
        print("All files already use typographic quotes and dashes.")


if __name__ == '__main__':
    main()
