#!/usr/bin/env python3
"""Compare gql-errors/*.adoc with content-nav.adoc and add missing nav entries."""

import os
import re
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
errors_dir = os.path.join(project_root, "modules", "ROOT", "pages", "errors", "gql-errors")
nav_file = os.path.join(project_root, "modules", "ROOT", "content-nav.adoc")

EXCLUDED = {"index", "auto-index"}
ENTRY_RE = re.compile(r"^\*{4} xref:errors/gql-errors/([^.\[]+)\.adoc\[\]\s*$")
SECTION_RE = re.compile(r"^\*{3} xref:errors/gql-errors/index\.adoc#")

# Section anchor in index.adoc for each SQLSTATE class prefix.
SECTIONS = {
    "08": "connection-exceptions",
    "22": "data-exceptions",
    "25": "invalid-transaction-state",
    "2D": "invalid-transaction-termination",
    "40": "transaction-rollback",
    "42": "syntax-error-or-access-rule-violation",
    "50": "general-processing-exceptions",
    "51": "system-configuration-or-operation-exceptions",
    "52": "procedure-exceptions",
    "53": "function-exceptions",
    "G1": "dependent-object-error",
}


def main():
    files = {
        f[:-5] for f in os.listdir(errors_dir)
        if f.endswith(".adoc") and f[:-5] not in EXCLUDED
    }

    with open(nav_file, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    nav = {m.group(1) for m in map(ENTRY_RE.match, lines) if m}

    missing = sorted(files - nav)
    stale = sorted(nav - files)

    print(f"Files in gql-errors: {len(files)}")
    print(f"Entries in content-nav.adoc: {len(nav)}")
    print(f"Missing from nav: {len(missing)}, stale in nav: {len(stale)}")

    if stale:
        print("In content-nav.adoc but no file exists (not modified):")
        for code in stale:
            print(f"  {code}")

    if not missing:
        print("content-nav.adoc is in sync.")
        return 0

    print("Files missing from content-nav.adoc:")
    unplaced = []
    for code in missing:
        anchor = SECTIONS.get(code[:2])
        start = next(
            (i for i, l in enumerate(lines)
             if SECTION_RE.match(l) and f"#{anchor}[" in l),
            None,
        ) if anchor else None
        if start is None:
            unplaced.append(code)
            continue

        # Section ends at next section header or a shallower entry.
        end = start + 1
        while end < len(lines) and lines[end].startswith("****"):
            end += 1

        pos = end
        for i in range(start + 1, end):
            m = ENTRY_RE.match(lines[i])
            if m and m.group(1) > code:
                pos = i
                break

        lines.insert(pos, f"**** xref:errors/gql-errors/{code}.adoc[]")
        print(f"  added {code} to '{anchor}' at line {pos + 1}")

    if unplaced:
        print("No matching section in content-nav.adoc, add manually:")
        for code in unplaced:
            print(f"  {code}")

    with open(nav_file, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"Updated {nav_file}: {len(missing) - len(unplaced)} entries added.")

    return 1 if unplaced else 0


if __name__ == "__main__":
    sys.exit(main())
