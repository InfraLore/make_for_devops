#!/usr/bin/env python3
"""
Migrate && and || line continuations from end-of-line to start-of-next-line
within Markdown code blocks.

Old style:          New style:
  cmd1 && \           cmd1 \
  cmd2            && cmd2 \
                  && cmd3

Usage: python scripts/fix-continuation-style.py [--dry-run]
"""

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "chapters/02-executable_readme.md",
    "chapters/03-make_fundamentals.md",
    "chapters/04-testing_and_validating.md",
    "chapters/05-variables_and_configuration.md",
    "chapters/08-advanced_make.md",
    "chapters/13-make_for_infrastructure_provisioning.md",
    "chapters/14-make_for_infrastructure_reliability.md",
    "chapters/15-make_for_monitoring_and_metrics.md",
    "chapters/16-make_for_logging_and_incident_response.md",
    "chapters/17-security_and_compliance_workflows.md",
    "chapters/19-troubleshooting_and_debugging_make_workflows.md",
    "chapters/20-the_future_of_make_in_devops.md",
    "chapters/21-make_as_your_personal_learning_tool.md",
    "chapters/Appendix_A-quick_reference_guide.md",
    "chapters/Appendix_B-migration_strategies.md",
    "chapters/Appendix_C-prompt_templates.md",
]

EXCLUDE_LINES = {
    # inside single-quoted sh -c string
    "chapters/21-make_as_your_personal_learning_tool.md": {249},
}

OPERATORS = ("&&", "||")

def in_code_block(state):
    return state.get("in_code", False)

def process_file(rel_path, dry_run=False):
    path = ROOT / rel_path
    orig = path.read_text().splitlines(keepends=True)
    lines = [line.rstrip("\n") for line in orig]
    result = []
    has_changes = False
    exclude = EXCLUDE_LINES.get(str(rel_path), set())
    state = {"in_code": False}
    skip_next = False

    for i, raw_line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue

        if raw_line is None:
            continue

        line = raw_line
        stripped = line.strip()
        line_no = i + 1

        # Track code block fences
        if re.match(r"^```", stripped):
            state["in_code"] = not state["in_code"]
            result.append(line)
            continue

        if not in_code_block(state):
            result.append(line)
            continue

        if line_no in exclude:
            result.append(line)
            continue

        if i + 1 >= len(lines) or lines[i + 1] is None:
            result.append(line)
            continue

        next_line = lines[i + 1]

        # Detect OP \ at end of line
        op_match = re.search(r"([&|]{2})\s+\\$", line.rstrip())
        if not op_match:
            result.append(line)
            continue

        operator = op_match.group(1)

        # Transform current line: remove OP before trailing \
        pat_remove_op = re.compile(r"\s*" + re.escape(operator) + r"\s+\\$")
        current_xformed = pat_remove_op.sub(r" \\", line.rstrip())

        # Transform continuation: prepend OP at start of meaningful content
        cont_stripped = next_line.lstrip()
        tab_match = re.match(r"^(\t*)", line)
        base_indent = tab_match.group(1) if tab_match else ""
        cont_xformed = f"{base_indent}{operator} {cont_stripped}"

        if dry_run:
            print(f"\n  {rel_path}:{line_no}")
            print(f"  - {line}")
            print(f"  - {next_line}")
            print(f"  + {current_xformed}")
            print(f"  + {cont_xformed}")
            result.append(line)
        else:
            result.append(current_xformed)
            result.append(cont_xformed)
            has_changes = True
            skip_next = True

    if not dry_run and has_changes:
        path.write_text("\n".join(result) + "\n")
        return True

    return has_changes

def main():
    dry_run = "--dry-run" in sys.argv
    changed = []

    for f in FILES:
        if process_file(f, dry_run=dry_run):
            changed.append(f)

    if dry_run:
        return

    if not changed:
        print("No changes made.")
        return

    print(f"\n{'='*60}")
    print(f"Modified {len(changed)} file(s):")
    for f in changed:
        print(f"  - {f}")
    print(f"{'='*60}")
    print()
    print("Spot-check recommended. Review the diff:")
    print()
    print("  git diff")
    print()
    print("Or hand off to an agent to complete the review pass:")
    print()
    print('  task "Review the continuation style changes in git diff. Make sure all && and || are at start of continuation lines, none were missed, and the quoted-string exclusion in chapter 21 is intact. Fix any issues found." --subagent-type general')
    print()

if __name__ == "__main__":
    main()
