#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.6.4 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 through add_1_6_3:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

What 1.6.4 needs (18 files, +368/-236). This is an incremental release:
  * Selection Expand / Contract / Feather now share one Size box and three
    icon buttons. The sheet's help is new.
  * The status bar appends the selection's feather, e.g. " · Feather 5 px".
  * The colour palette's Reset button became a swatch below the colours, with
    a new help string. "Reset colors" and the swap/default help strings
    already exist.

Deliberately NOT translated:
  * The Canvas drawing code in LassoControls (SelectionModifyIcon) has no
    user-visible strings.
  * SelectionFeatherTests / SelectionTests assert behaviour, not UI text.
"""

import datetime
import json
import os
import shutil
import sys

import os as _os
REPO = _os.environ.get("COMPOSITOR_CN_REPO") or _os.path.abspath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
CATALOG = os.path.join(REPO, "Compositor/Localizable.xcstrings")
BACKUP_DIR = _os.environ.get("COMPOSITOR_CN_LOCALIZATION_BACKUPS") or _os.path.join(
    REPO, "tools/localization/backups")

TRANSLATIONS = {
    "How many pixels to expand, contract or feather the selection by":
        "扩展、收缩或羽化选区时的像素数",
    " · Feather %lld px": " · 羽化 %lld 像素",
    "Reset colors to black and white (D)": "重置为黑白 (D)",
}

OBSOLETE = {}


def still_referenced(snippet: str) -> bool:
    """True if any Swift source outside the catalog still spells this key."""
    for root, _dirs, files in os.walk(REPO):
        if "/.git" in root or "build-logs" in root or "DerivedData" in root:
            continue
        for name in files:
            if not name.endswith(".swift"):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    if snippet in handle.read():
                        return True
            except (UnicodeDecodeError, OSError):
                continue
    return False


def main() -> int:
    with open(CATALOG, "rb") as handle:
        original = handle.read()

    if b"<<<<<<<" in original or b">>>>>>>" in original:
        print("ABORT: the catalog still holds merge conflict markers.", file=sys.stderr)
        return 1

    catalog = json.loads(original.decode("utf-8"))

    probe = json.dumps(catalog, indent=2, ensure_ascii=False)
    if probe.encode("utf-8") != original:
        print("ABORT: re-serialising the catalog does not reproduce the original bytes.",
              file=sys.stderr)
        print("Refusing to rewrite the file; inspect its formatting first.", file=sys.stderr)
        return 1

    strings = catalog["strings"]
    added, filled, skipped = [], [], []
    for key, value in TRANSLATIONS.items():
        if key not in strings:
            strings[key] = {
                "localizations": {
                    "zh-Hans": {"stringUnit": {"state": "translated", "value": value}}
                }
            }
            added.append(key)
            continue
        entry = strings[key].setdefault("localizations", {})
        if "zh-Hans" in entry:
            skipped.append(key)
            continue
        entry["zh-Hans"] = {"stringUnit": {"state": "translated", "value": value}}
        filled.append(key)

    removed, kept = [], []
    for key, snippet in OBSOLETE.items():
        if key not in strings:
            continue
        if still_referenced(snippet):
            kept.append(key)
            continue
        del strings[key]
        removed.append(key)

    if not (added or filled or removed):
        print("Nothing to do (all keys present, no obsolete ones left).")
        return 0

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"Localizable.xcstrings.{stamp}.bak")
    shutil.copy2(CATALOG, backup)

    with open(CATALOG, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(catalog, indent=2, ensure_ascii=False))

    print(f"backup: {backup}")
    print(f"added {len(added)}, filled {len(filled)}, skipped {len(skipped)}, removed {len(removed)}")
    for key in added:
        print(f"  + {key[:72]}  ->  {TRANSLATIONS[key][:36]}")
    for key in filled:
        print(f"  ~ (filled zh-Hans) {key[:72]}")
    for key in skipped:
        print(f"  = (already translated) {key[:72]}")
    for key in removed:
        print(f"  - {key[:72]}")
    for key in kept:
        print(f"  ! kept, still referenced in source: {key[:60]}")
    print(f"total keys now: {len(strings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
