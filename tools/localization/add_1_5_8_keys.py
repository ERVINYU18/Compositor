#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.5.8 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 / 1_4_10 / 1_5_3 / 1_5_5 / 1_5_6 / 1_5_7:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

What 1.5.8 changed (7 files, 8 commits):
  * Lens Effects' Prism is reworked: "Reach" (`prismSpread`) is gone, replaced by
    "Blur" (`prismBlur`) and a One Way / Both Ways "Direction" picker
    (`prismBothWays`). Four strings die with it, four are new.
  * Threshold now runs to 100, and its two help texts gained a clause.
  * Prism's Angle help was reworded.
  * ProjectStore accepts every format version from 1 through `current`; the
    `upstreamVersions` range is gone, so the version error's format string lost
    two of its four placeholders.

Deliberately NOT translated:
  * `LensEffect` / `BokehShape` raw values stay English; only the catalog
    supplies Chinese (`Text(verbatim: $0.localizedName)`).
  * "%" and "°" units stay as they are.
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
    # --- Prism: the new Blur slider and the Direction picker ---
    "Direction": "方向",
    "One Way": "单向",
    "Both Ways": "双向",

    # --- Prism: help texts ---
    "Which way the copies step":
        "重影偏移的方向",
    "Soften the copies, more the farther they're pushed":
        "柔化重影，偏移越远越柔和",
    "Copies to one side of the picture, or out to both":
        "重影只出现在画面一侧，或向两侧同时延伸",

    # --- Threshold now reaches 100, so its help says what the top of the range means ---
    "How bright a light has to be to flare; near 100, only the biggest, brightest spots":
        "光线要多亮才会产生光晕；接近 100 时只保留最大最亮的光源",
    "How bright a light has to be to sparkle; near 100, only the biggest, brightest spots":
        "光线要多亮才会产生星芒；接近 100 时只保留最大最亮的光源",

    # --- ProjectError.version: 1 through `current`, plus 27 ---
    "This project uses format version %lld. This app supports versions 1–%lld and 27.":
        "此项目使用的格式版本为 %lld。本 App 支持版本 1–%lld 和 27。",
}

# Keys that died with upstream's rework. Only remove them once nothing in the
# repo still spells them; the script checks before dropping each one.
OBSOLETE = {
    "Reach": '"Reach"',  # prismSpread's slider label
    "How far into the frame the copies show from that edge": '"How far into the frame the copies show from that edge"',
    "Which way it's pushed, toward the edge the prism sits at": '"Which way it\'s pushed, toward the edge the prism sits at"',
    "This project uses format version %lld. This app supports versions %lld–%lld, 27, and %lld.":
        "versions %lld–%lld, 27, and %lld",
}


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
