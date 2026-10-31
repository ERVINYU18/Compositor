#!/usr/bin/env python3
"""Add the zh-Hans entries v1.4.5 needs.

Two gaps found by the four-class audit plus a sweep of helper-argument labels:
  * 5 new .help() tooltips (the CRT/scanlines filter and the blur radius)
  * 6 parameter labels passed to the FilterSheet control(_:) helper, which renders
    them with localizedString — 2 new in v1.4.5, 4 pre-existing.
Every key is verified to exist in the named source file before writing.
"""
import json
import os
import shutil
import sys

import os as _os
REPO = _os.environ.get("COMPOSITOR_CN_REPO") or _os.path.abspath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
CATALOG = os.path.join(REPO, "Compositor/Localizable.xcstrings")
BACKUP = "/Users/yi/Desktop/AI/DSH/Compositor CN/01-merge-scene-evidence/Localizable.xcstrings.before-1.4.5"

FS = "Compositor/UI/FilterSheet.swift"
BC = "Compositor/UI/BrushControls.swift"

# key -> (translation, file it must appear in, substring to verify)
ENTRIES = {
    # --- 5 new help tooltips -------------------------------------------------
    "How far apart the screen's lines are":
        ("屏幕扫描线之间的间距", FS, 'help("How far apart the screen\'s lines are")'),
    "Light blooming around the lines, like a CRT's phosphors":
        ("线条周围的辉光，如同 CRT 荧光粉", FS,
         'help("Light blooming around the lines, like a CRT\'s phosphors")'),
    "Break the lines into glowing beads":
        ("把扫描线分解为发光颗粒", FS, 'help("Break the lines into glowing beads")'),
    "Make the lines waver sideways down the screen, like a CRT losing sync":
        ("让扫描线沿屏幕向下摆动，如同 CRT 失去同步", FS,
         'help("Make the lines waver sideways down the screen, like a CRT losing sync")'),
    "How far the blur softens, in pixels":
        ("模糊柔化的范围（像素）", BC, 'help("How far the blur softens, in pixels")'),

    # --- 6 parameter labels --------------------------------------------------
    "Line Spacing":       ("扫描线间距", FS, 'control("Line Spacing"'),
    "Wobble":             ("摆动",       FS, 'control("Wobble"'),
    "Refine":             ("细化",       FS, 'control("Refine"'),
    "Shift Edge":         ("边缘位移",   FS, 'control("Shift Edge"'),
    "Remove Distortion":  ("去除畸变",   FS, 'control("Remove Distortion"'),
    "Text Size":          ("文字大小",   FS, 'control("Text Size"'),
}


def main():
    # every key must appear in its source file
    problems = []
    for key, (_v, rel, marker) in ENTRIES.items():
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            problems.append(f"missing file {rel}")
        elif marker not in open(path, encoding="utf-8").read():
            problems.append(f"NOT IN SOURCE {rel}: {key!r}")
    if problems:
        print("ABORT: source verification failed")
        for p in problems:
            print("   ", p)
        return 1
    print(f"source verification : {len(ENTRIES)}/{len(ENTRIES)} keys found verbatim")

    raw = open(CATALOG, encoding="utf-8").read()
    doc = json.loads(raw)
    if json.dumps(doc, indent=2, ensure_ascii=False) + "\n" != raw:
        print("ABORT: serializer would not round-trip byte-identically")
        return 1

    shutil.copy2(CATALOG, BACKUP)
    strings = doc["strings"]
    added, already = [], []
    for key, (value, _rel, _m) in ENTRIES.items():
        if key in strings:
            already.append(key)
            continue
        strings[key] = {
            "localizations": {"zh-Hans": {"stringUnit": {"state": "translated", "value": value}}}
        }
        added.append(key)

    out = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    open(CATALOG, "w", encoding="utf-8").write(out)

    check = json.load(open(CATALOG, encoding="utf-8"))
    bad = [k for k in added
           if not (((check["strings"][k].get("localizations") or {}).get("zh-Hans") or {})
                   .get("stringUnit") or {}).get("value")]
    print(f"added               : {len(added)}")
    print(f"already present     : {len(already)} {already if already else ''}")
    print(f"total keys now      : {len(check['strings'])}")
    print(f"re-serialization stable : {json.dumps(check, indent=2, ensure_ascii=False) + chr(10) == out}")
    print(f"failing verify      : {len(bad)} {bad if bad else ''}")
    return 0 if not bad and not already else 2


if __name__ == "__main__":
    sys.exit(main())
