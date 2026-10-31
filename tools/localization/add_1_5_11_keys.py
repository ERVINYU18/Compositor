#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.5.11 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 / 1_4_10 / 1_5_3 / 1_5_5 / 1_5_6 / 1_5_7 / 1_5_8 / 1_5_9:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

What 1.5.11 needs (34 files, 797 insertions). v1.5.10 was never merged on its
own — the updater jumped 1.5.9 -> 1.5.11 — so this round carries both releases:

  * Layer alignment: a new `LayerAlign.swift` with `LayerAlignment` and
    `LayerDistribution`, shown in the Layer menu, in the Move bar's Align
    popover, and as undo-step names. Their raw values collide across the two
    enums ("Horizontal Centers" is both an align and a distribute), and the two
    read differently in Chinese (居中*对齐* vs 居中*分布*), so each case gets its
    own "Align ..." / "Distribute ..." key instead of `localizedName`.
  * Crop: a custom-ratio popover (Custom…, Custom ratio, Width:Height, two
    hints), and the ratio list regrouped with "Canvas" replacing "Original".
  * Sharpen: a new filter and adjustment kind, plus its two controls.
  * Lens Effects: a new "Fringe" control.
  * Move bar: the flip buttons became icon-only, with "Flip Horizontal" /
    "Flip Vertical" help and accessibility labels.

Also fixed this round, pre-existing leaks the string audit cannot see (enum raw
values that reach the screen through a String overload, not a literal):
  * `ShapeLineStyle` / `ShapeLineCap` raw values shown in the Line tool's Style
    and Cap menus, and read out as accessibility labels. 1.5.9's note claimed
    they were never menu titles; that was wrong. Caps get their own keys because
    the catalog's "Square" / "Round" are shapes (正方形 / 圆形), which read wrong
    for how a line's ends are finished.
  * `ChannelPack.Channel` raw values, shown as the Channel Pack rows' names and
    as each row's picker label.
  * The colour picker's R/G/B accessibility labels.

Deliberately NOT translated (checked this round):
  * `LineSample` image cache keys ("style.Solid", "cap.Round") — never shown.
  * `Alpha` is used only as a channel name here; "透明度" is what a Chinese
    Channel Pack panel calls it.
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
    # --- Layer menu + Move bar: Align / Distribute ---
    "Align": "对齐",
    "Distribute": "分布",
    "Align Left Edges": "左边缘对齐",
    "Align Horizontal Centers": "水平居中对齐",
    "Align Right Edges": "右边缘对齐",
    "Align Top Edges": "上边缘对齐",
    "Align Vertical Centers": "垂直居中对齐",
    "Align Bottom Edges": "下边缘对齐",
    "Distribute Horizontal Centers": "水平居中分布",
    "Distribute Vertical Centers": "垂直居中分布",
    "Distribute Horizontal Spacing": "水平间隔分布",
    "Distribute Vertical Spacing": "垂直间隔分布",
    "%@ (three or more layers)": "%@（三个或更多图层）",
    "Line layers up with each other, the selection, or the canvas when one is selected":
        "让图层彼此对齐，或与选区对齐；只选中一个图层时与画布对齐",
    # --- Crop: custom ratio popover ---
    "Custom…": "自定义…",
    "Custom ratio": "自定义比例",
    "Width:Height": "宽度:高度",
    "Width:height, such as 4:5 or 3:2": "宽:高，例如 4:5 或 3:2",
    "Enter a positive ratio within the document size limits.": "请输入文档尺寸范围内的正数比例。",
    # --- Sharpen ---
    "Sharpen": "锐化",
    "How strongly edges and fine detail are brought out": "边缘与细节被强化的程度",
    "How fine the detail it sharpens: small for crisp texture, larger for a punchier look":
        "锐化的细节有多细：数值小则纹理锐利，数值大则观感更有冲击力",
    # --- Lens Effects: Fringe ---
    "Fringe": "色散",
    "Split each copy's red and blue apart, as glass does; 0 keeps the copies crisp":
        "像玻璃那样把每个副本的红蓝分开；0 则保持副本清晰",
    # --- Line tool: Style and Cap menus ---
    "Solid": "实线",
    "Dotted": "点线",
    "Dashed": "虚线",
    "Long Dash": "长虚线",
    "Round Cap": "圆头",
    "Square Cap": "方头",
    # --- Channel Pack rows ---
    "Alpha": "透明度",
}

# Nothing dies in 1.5.11: upstream only added to the UI.
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
