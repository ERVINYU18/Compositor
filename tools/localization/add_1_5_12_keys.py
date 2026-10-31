#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.5.12 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 / 1_4_10 / 1_5_3 / 1_5_5 / 1_5_6 / 1_5_7 / 1_5_8 /
1_5_9 / 1_5_11:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

What 1.5.12 needs (10 files, 662 insertions). One feature, Rim Light:

  * `FilterKind.rimLight` — the menu title and the sheet's undo-step name come
    from `localizedName`, i.e. `localizedString(rawValue)`, so the key is the
    raw value "Rim Light".
  * `FilterSheet.rimLightControls` — Glow, then per light: its number as a
    heading, a colour well, and Angle / Strength / Width / Choke, plus
    Add Light and a remove button. "Glow", "Angle", "Strength" and "Width"
    already have entries (辉光 / 角度 / 强度 / 宽度); "Choke" does not — and the
    audit's sink regex skips `control("Choke", ...)` because the line holds no
    `Text(` or `.help(`, so it has to be found by hand.
  * The first preview finds the subject through Vision, which takes a moment:
    "Finding the subject…".
  * `ColorPickerTarget` gained `.rimLight(index:)` and upstream shortened the
    dither titles from "Dither Light Color" to "Light Color", so both dither
    keys are replaced (see OBSOLETE).

Deliberately NOT translated (checked this round):
  * Everything in `RimLight.swift` and `MetalRimLight.swift` that looks like a
    string is a Core Image filter name ("CIColorMatrix", "CIDivideBlendMode")
    or a Metal function name ("rimLight", "rimCombine"). Neither reaches the UI.
  * `RimLightSettings` is `Equatable, Sendable` — not Codable, not in `.comp`,
    same as `LensEffectSettings` was before 1.5.9 — which is why upstream could
    add it to `FilterSettings` without bumping the project format (still 20).
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
    # --- Filter menu + sheet title ---
    "Rim Light": "轮廓光",
    # --- Rim Light controls ---
    "Choke": "收缩",
    "Light %lld": "光源 %lld",
    "Add Light": "添加光源",
    "Choose this light's color": "选择此光源的颜色",
    "Remove this light": "移除此光源",
    "How far the light wraps around the subject's edges": "光线环绕主体边缘的范围",
    "How the light ends on the inside: low feathers it off softly from the edge, high holds it bright and ends it crisply":
        "光线在主体内侧的收尾方式：数值低时从边缘柔和淡出，数值高时保持明亮并干脆收住",
    "Let the lights glow in the air around the subject, blending them into the background":
        "让光线在主体周围的空气中发光，与背景融为一体",
    "Light the subject from another side as well": "再从另一侧为对象打光",
    "Where the light comes from, behind the subject: 0° from the right, 90° from above":
        "光线来自主体后方的哪个方向：0° 在右侧，90° 在上方",
    "Finding the subject…": "正在查找主体…",
    # --- Colour picker ---
    "Color Picker (Light %lld)": "拾色器（光源 %lld）",
    "Color Picker (Light Color)": "拾色器（亮色）",
    "Color Picker (Dark Color)": "拾色器（暗色）",
}

# Upstream dropped the "Dither" qualifier from these two titles. Nothing else
# spells them, so they go rather than linger as dead weight.
OBSOLETE = {
    "Color Picker (Dither Light Color)": "Color Picker (Dither Light Color)",
    "Color Picker (Dither Dark Color)": "Color Picker (Dither Dark Color)",
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
