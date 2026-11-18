#!/usr/bin/env python3
"""Assert the text tool's icon stays a literal letter T, in both places it is drawn.

Why this is a script and not a unit test: the rule is about source shape, not runtime
behaviour. macOS substitutes the `textformat` SF Symbol with a localized glyph drawn
in the bundle's language ("格式" under zh-Hans), so the only correct implementations
are hand-drawn letters. A unit test would have to launch the app under zh-Hans and
inspect pixels — this asserts the invariant directly and fails on the exact regression
(v1.6.7's rail rework silently reintroducing `textformat` for .type).

Two carriers must hold:
  - Compositor/UI/ToolRail.swift       — the rail's .type button draws TextToolIcon
  - Compositor/UI/NativeLayerList.swift — the text layer's badge draws a literal T

Exit codes: 0 = OK, 1 = regression found. Writes tools/localization/text-t-icon-result.json.
"""
import json
import os
import re
import sys

REPO = os.environ.get("COMPOSITOR_CN_REPO") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

RAIL = "Compositor/UI/ToolRail.swift"
BADGE = "Compositor/UI/NativeLayerList.swift"


def read(rel):
    path = os.path.join(REPO, rel)
    try:
        return open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"FAIL: cannot read {rel}: {e}")
        sys.exit(1)


def check_rail(src):
    """The rail must route .type to TextToolIcon and never to an SF Symbol."""
    problems = []

    # 1. The .type branch exists and draws TextToolIcon.
    if not re.search(r'if\s+tool\s*==\s*\.type\s*\{[^\n]*TextToolIcon\(\)', src):
        problems.append(
            "the .type branch no longer draws TextToolIcon() — "
            "the rail falls through to the SF Symbol path, which renders "
            '"格式" under zh-Hans'
        )

    # 2. No SF Symbol is drawn for .type. The historical bug was `textformat`.
    for pat, why in (
        (r'\.type\s*[?:].*"textformat"', '.type is mapped to the "textformat" SF Symbol'),
        (r'"textformat".*\.type', '"textformat" is used in a .type expression'),
    ):
        if re.search(pat, src):
            problems.append(f'{why} — macOS localizes that glyph to "格式"')

    # 3. TextToolIcon draws a verbatim T, never a localizable Text/catalog key.
    m = re.search(r'struct\s+TextToolIcon\s*:\s*View\s*\{', src)
    if not m:
        problems.append("struct TextToolIcon is gone")
    else:
        body = src[m.end():m.end() + 600]
        if 'Text(verbatim: "T")' not in body:
            problems.append(
                'TextToolIcon does not draw Text(verbatim: "T") — '
                "a plain Text(\"T\") goes through the catalog and can be translated"
            )
        if re.search(r'Image\s*\(\s*systemName', body):
            problems.append("TextToolIcon draws an SF Symbol, not the letter")

    return problems


def check_badge(src):
    """The layer-list badge must draw a literal T too."""
    problems = []
    m = re.search(r'static\s+let\s+textLayerIcon', src)
    if not m:
        problems.append("NativeLayerList.textLayerIcon is gone — text layers lose the T badge")
        return problems

    body = src[m.end():m.end() + 900]
    if '"T"' not in body:
        problems.append("textLayerIcon does not draw the letter T")
    if 'textformat' in body:
        problems.append('textLayerIcon references "textformat" — that glyph is localized to "格式"')
    return problems


def main():
    findings = {
        RAIL: check_rail(read(RAIL)),
        BADGE: check_badge(read(BADGE)),
    }
    total = sum(len(v) for v in findings.values())

    print("Compositor-CN text tool T-icon invariant")
    print("=" * 64)
    for rel, problems in findings.items():
        print(f"{rel}: {'OK' if not problems else f'{len(problems)} problem(s)'}")
    print()

    for rel, problems in findings.items():
        if problems:
            print(f"--- {rel} ---")
            for p in problems:
                print(f"  x {p}")
            print()

    if total == 0:
        print('OK: the text tool icon is a literal T in both places.')
    else:
        print(f"FAIL: {total} problem(s). The letter T must never be localized.")

    out = os.path.join(REPO, "tools/localization/text-t-icon-result.json")
    json.dump({"findings": findings, "total_problems": total},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
