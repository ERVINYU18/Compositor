#!/usr/bin/env python3
"""Audit Compositor-CN sources for user-facing string literals missing from Localizable.xcstrings.

Read-only: scans Swift sources and reports literals that reach a UI sink but have no
catalog entry, which is the root cause of "dynamic English" leaking into the Chinese build.
"""
import json
import os
import re
import sys

import os as _os
REPO = _os.environ.get("COMPOSITOR_CN_REPO") or _os.path.abspath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
CATALOG = os.path.join(REPO, "Compositor/Localizable.xcstrings")
SRC_DIRS = [os.path.join(REPO, "Compositor")]

# A Swift string literal, single line, no interpolation. Captures the raw body.
LITERAL = re.compile(r'"((?:[^"\\\n]|\\.)*)"')

# Sinks whose argument is shown to the user. Context look-behind windows.
SINKS = [
    (re.compile(r'localizedString\(\s*$'), "localizedString"),
    (re.compile(r'NSLocalizedString\(\s*$'), "NSLocalizedString"),
    (re.compile(r'\bText\(\s*$'), "Text"),
    (re.compile(r'\bButton\(\s*$'), "Button"),
    (re.compile(r'\bLabel\(\s*$'), "Label"),
    (re.compile(r'\bToggle\(\s*$'), "Toggle"),
    (re.compile(r'\bTextField\(\s*$'), "TextField"),
    (re.compile(r'\bSecureField\(\s*$'), "SecureField"),
    (re.compile(r'\bPicker\(\s*$'), "Picker"),
    (re.compile(r'\bMenu\(\s*$'), "Menu"),
    (re.compile(r'\bSection\(\s*$'), "Section"),
    (re.compile(r'\.navigationTitle\(\s*$'), "navigationTitle"),
    (re.compile(r'NSMenuItem\(title:\s*$'), "NSMenuItem.title"),
    (re.compile(r'NSMenu\(title:\s*$'), "NSMenu.title"),
    (re.compile(r'\.toolTip\s*=\s*$'), "toolTip"),
    (re.compile(r'accessibilityLabel\(\s*$'), "accessibilityLabel"),
    (re.compile(r'help\(\s*$'), "help"),
    (re.compile(r'alert\(\s*$'), "alert"),
    (re.compile(r'setAccessibilityLabel\(\s*$'), "setAccessibilityLabel"),
]

VERBATIM = re.compile(r'\bText\(verbatim:\s*$')


def find_blocks(src):
    """Yield (literal, context_before, line_no, kind)."""
    out = []
    for m in LITERAL.finditer(src):
        body = m.group(1)
        before = src[max(0, m.start() - 90):m.start()]
        line = src.count("\n", 0, m.start()) + 1
        # skip if the literal itself contains interpolation
        if "\\(" in body:
            continue
        kind = None
        if VERBATIM.search(before):
            kind = "VERBATIM(ok)"
        else:
            for rx, name in SINKS:
                if rx.search(before):
                    kind = name
                    break
        if kind:
            out.append((body, before, line, kind))
    return out


def main():
    catalog = json.load(open(CATALOG, encoding="utf-8"))
    keys = set(catalog["strings"])
    entries = catalog["strings"]

    missing = {}       # literal -> list of (file, line, kind)
    verbatim = {}
    untranslated = {}  # key present but no zh-Hans

    for d in SRC_DIRS:
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.endswith(".swift"):
                    continue
                path = os.path.join(root, fn)
                rel = os.path.relpath(path, REPO)
                try:
                    src = open(path, encoding="utf-8").read()
                except UnicodeDecodeError:
                    continue
                for body, _before, line, kind in find_blocks(src):
                    if kind.startswith("VERBATIM"):
                        verbatim.setdefault(body, []).append((rel, line))
                        continue
                    if body not in keys:
                        missing.setdefault(body, []).append((rel, line, kind))

    for k, v in entries.items():
        zh = (v.get("localizations") or {}).get("zh-Hans") or {}
        if not (zh.get("stringUnit") or {}).get("value"):
            untranslated[k] = True

    print("=" * 72)
    print("Compositor-CN string audit")
    print("=" * 72)
    print(f"catalog keys          : {len(keys)}")
    print(f"keys lacking zh-Hans  : {len(untranslated)}")
    print(f"UI literals NOT in catalog: {len(missing)}")
    print(f"Text(verbatim:) literals  : {len(verbatim)}")
    print()

    if missing:
        print("--- MISSING FROM CATALOG (would render as English) ---")
        for lit in sorted(missing, key=lambda s: (-len(missing[s]), s)):
            locs = missing[lit]
            print(f'  "{lit}"  ({len(locs)} site{"s" if len(locs) != 1 else ""})')
            for rel, line, kind in locs[:4]:
                print(f"        {rel}:{line}  [{kind}]")
            if len(locs) > 4:
                print(f"        ... +{len(locs) - 4} more")
        print()

    if verbatim:
        print("--- Text(verbatim:) — intentionally untranslated (review) ---")
        for lit in sorted(verbatim):
            locs = verbatim[lit]
            print(f'  "{lit}"')
            for rel, line in locs[:3]:
                print(f"        {rel}:{line}")
        print()

    if untranslated:
        print("--- catalog keys lacking zh-Hans ---")
        for k in sorted(untranslated):
            print(f'  "{k}"')
        print()

    json.dump(
        {
            "catalog_keys": len(keys),
            "missing": {k: v for k, v in missing.items()},
            "verbatim": {k: v for k, v in verbatim.items()},
            "untranslated": sorted(untranslated),
        },
        open(os.path.join(REPO, "tools/localization/audit-result.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
