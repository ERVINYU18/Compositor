#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.5.9 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 / 1_4_10 / 1_5_3 / 1_5_5 / 1_5_6 / 1_5_7 / 1_5_8:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

What 1.5.9 needs (26 files, 9 commits):
  * Upstream's UI text is all rework of existing strings, not new copy: the
    Filter menu splits into "those that can also be adjustment layers" and the
    rest, and Vignette / Lens Effects / Tonal Contrast become adjustment kinds.
    Their names already have zh-Hans from 1.5.7 (晕影 / 镜头效果 / 色调对比度),
    and `AdjustmentKind` reaches the catalog through `localizedName`.
  * The one real gap is `RGB Split`, which has been missing since 1.5.7: both
    `FilterKind` and `AdjustmentKind` spell it as a raw value and show it
    through `localizedName`, so it was rendering in English.

Deliberately NOT translated (checked this round, all reach the screen in a
form that is already translated, or are internal):
  * `Adjustment input` — an internal `ImportedImage` name for the scratch layer
    that feeds an adjustment's histogram; the layer never enters the manifest.
  * `Frame delay` / `Same for all` — `GIFFrameTiming` raw values; the timeline
    builds its own millisecond and `· Original` labels instead.
  * `Solid` / `Dotted` / `Dashed` / `Long Dash` — `ShapeLineStyle` raw values
    used for dash patterns, not shown as menu titles.
  * `CMYK Profiles` — a directory name on disk, matched exactly.
  * `Drag to paint` / `Drag to erase` — substrings of one long `localizedString`
    key whose full text is already translated.
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
    # --- RGB Split: a filter and an adjustment kind, shown through localizedName ---
    "RGB Split": "RGB 分离",
}

# Nothing dies in 1.5.9: upstream only reshaped existing strings.
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

    # Prove the round-trip is byte-identical before we change anything.
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
