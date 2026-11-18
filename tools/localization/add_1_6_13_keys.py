#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.6.13 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 .. add_1_6_6:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly;
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * refuse to run while merge conflict markers remain.

What v1.6.13 needs (carries v1.6.8 through v1.6.12):
  * Export As gains PSD export (summary text, format hint, "Changes" row).
  * The shape tool gains a stroke picker and per-line colour/width/dash/cap
    help strings; several were already present from earlier rounds.

Deliberately NOT translated (verified present in the catalog already):
  Stroke, Width, Fill, Color, Style, Cap, Radius, Smooth Corners,
  Fill color, and most help sentences carried over from v1.6.7.

The letter T (ToolRail.TextToolIcon) stays a literal identifier.
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
    # Export As — PSD export (new in this round)
    "Changes": "更改",
    "Layers, folders and masks kept · sRGB": "保留图层、文件夹和蒙版 · sRGB",
    "Other formats: TIFF, PDF, GIF and PSD to keep the layers, EXR to keep light brighter than white, and Channel Pack for game textures": "其他格式：TIFF、PDF、GIF，以及可保留图层的 PSD；EXR 可保留比白色更亮的光；Channel Pack 用于游戏纹理",
    "Other formats: TIFF, PDF, GIF and PSD to keep the layers, and Channel Pack for game textures": "其他格式：TIFF、PDF、GIF，以及可保留图层的 PSD；Channel Pack 用于游戏纹理",
    # Shape tool — colour picker / stroke help (new in this round)
    "Color of the selected line": "所选线条的颜色",
    "Color of the next line": "下一条线条的颜色",
    "Fill color of the selected shape": "所选形状的填充颜色",
    "Stroke color": "描边颜色",
    "Stroke drawn inside the shape, in pixels. 0 draws none": "在形状内侧绘制的描边，单位为像素；0 表示不绘制",
    "Dashes of the selected line; they grow with its width": "所选线条的虚线；长度随线宽增加",
    "How this line's ends are finished": "此线条两端的收尾方式",
    "Round this rectangle's corners by this many pixels; 0 keeps them square": "以指定像素数圆化此矩形的角；0 表示保持直角",
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
    # The catalog may or may not end with a newline; accept whichever is there
    # as long as re-serialising reproduces it byte-for-byte.
    reserialised = (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    reserialised_nonl = json.dumps(catalog, ensure_ascii=False, indent=2).encode("utf-8")
    if reserialised != original and reserialised_nonl != original:
        print("ABORT: re-serialising the untouched catalog changes its bytes.", file=sys.stderr)
        return 1
    trailing_nl = reserialised == original

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"Localizable.xcstrings.pre-1.6.13-{stamp}.json")
    shutil.copy2(CATALOG, backup)
    print(f"backup: {backup}")

    strings = catalog.setdefault("strings", {})

    for key, zh in TRANSLATIONS.items():
        entry = strings.setdefault(key, {})
        loc = entry.setdefault("localizations", {})
        zh_entry = loc.setdefault("zh-Hans", {})
        zh_entry["stringUnit"] = {"state": "translated", "value": zh}
        print(f"  + {key!r}: {zh}")

    for key in OBSOLETE:
        if still_referenced(key):
            print(f"  ! keep {key!r}: still referenced")
            continue
        strings.pop(key, None)
        print(f"  - {key!r}")

    payload = json.dumps(catalog, ensure_ascii=False, indent=2)
    if trailing_nl:
        payload += "\n"
    with open(CATALOG, "w", encoding="utf-8") as handle:
        handle.write(payload)

    print(f"OK: catalog now has {len(strings)} keys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
