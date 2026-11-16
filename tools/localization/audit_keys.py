#!/usr/bin/env python3
"""Audit the blind spots that audit_strings.py cannot see.

audit_strings.py uses a short look-behind window for known UI sinks. It misses
keys carried to the screen indirectly:

  1. `var titleKey: LocalizedStringKey { case .a: "A" ... }` — the literal is
     returned by a computed property, never passed straight to Text(...).
  2. `-> LocalizedStringKey` functions with the same pattern.
  3. Ternary expressions whose branches are literals, e.g.
     `Text(isOn ? "Pause" : "Play")`.

The `Text` layer-type key was missing from v1.6.4 through v1.6.7 precisely
because of #1: audit_strings.py reported 0 gaps for four rounds.

Read-only. Writes a JSON result next to audit_strings.py's output for the
updater gate and CI to consume.

Exit code: 0 when every literal has a catalog key, 1 when gaps are found.
"""

import json
import os
import re
import sys
from pathlib import Path

REPO = os.environ.get("COMPOSITOR_CN_REPO") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
CATALOG = Path(REPO) / "Compositor/Localizable.xcstrings"
SRC = Path(REPO) / "Compositor"

LITERAL = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def catalog_keys():
    if not CATALOG.exists():
        return set()
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    return set(data.get("strings", {}).keys())


def is_catalog_candidate(literal):
    """Interpolated strings and punctuation-only strings never belong in the catalog."""
    if not literal or "\\(" in literal:
        return False
    return any(ch.isalnum() for ch in literal)


def localized_string_key_bodies(source):
    """Bodies of `var x: LocalizedStringKey { ... }` and `-> LocalizedStringKey { ... }`."""
    # Non-greedy to the first closing brace at 4/8 spaces; SwiftUI computed
    # properties in this codebase follow that indentation. Deliberately
    # conservative: a false negative here only means the manual sweep still
    # has to run, a false positive would be a bogus blocker.
    yield from re.finditer(
        r':\s*LocalizedStringKey\s*\{(.*?)\n\s{4,8}\}', source, re.S
    )
    yield from re.finditer(
        r'->\s*LocalizedStringKey\s*\{(.*?)\n\s{4,8}\}', source, re.S
    )


def ternary_literals(source):
    """String literals inside a single-line ternary expression."""
    for line in source.split("\n"):
        if "?" not in line or ":" not in line:
            continue
        # Skip comments and lines localizedString() already handles.
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        if "localizedString(" in line:
            continue
        # Sinks that put the ternary's result on screen.
        if not re.search(r'\b(Text|Button|Label|Toggle|Picker|Menu)\s*\(', line):
            continue
        yield from LITERAL.findall(line)


def main():
    keys = catalog_keys()
    findings = {"localized_string_key": {}, "ternary": {}}

    for path in sorted(SRC.rglob("*.swift")):
        source = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO).as_posix()

        for match in localized_string_key_bodies(source):
            body = match.group(1)
            for literal in LITERAL.findall(body):
                if is_catalog_candidate(literal) and literal not in keys:
                    findings["localized_string_key"].setdefault(literal, []).append(rel)

        for literal in ternary_literals(source):
            if is_catalog_candidate(literal) and literal not in keys:
                findings["ternary"].setdefault(literal, []).append(rel)

    total = sum(len(v) for category in findings.values() for v in category.values())

    print("=" * 64)
    print("Compositor-CN key-carrier audit")
    print("=" * 64)
    print(f"catalog keys                 : {len(keys)}")
    print(f"LocalizedStringKey gaps      : {len(findings['localized_string_key'])}")
    print(f"ternary-expression gaps      : {len(findings['ternary'])}")
    print()

    for category, label in (
        ("localized_string_key", "--- LocalizedStringKey-carried literals NOT in catalog ---"),
        ("ternary", "--- ternary-carried literals NOT in catalog ---"),
    ):
        if findings[category]:
            print(label)
            for literal, files in sorted(findings[category].items()):
                print(f'  "{literal}"')
                for f in sorted(set(files)):
                    print(f"        {f}")
            print()

    if total == 0:
        print("OK: no key-carrier gaps found.")
    else:
        print(f"FAIL: {total} key-carrier gap(s).")

    json.dump(
        {
            "catalog_keys": len(keys),
            "localized_string_key": findings["localized_string_key"],
            "ternary": findings["ternary"],
            "total_gaps": total,
        },
        open(Path(REPO) / "tools/localization/audit-keys-result.json", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
