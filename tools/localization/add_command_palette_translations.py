#!/usr/bin/env python3
"""Add zh-Hans for the command palette (upstream 1.4.7) to Localizable.xcstrings.

Follows the convention of apply_translations.py:
  * back up the catalog before touching it;
  * refuse to write unless re-serialising the *untouched* catalog reproduces the
    original bytes exactly (proves the round-trip is byte-identical);
  * append new keys at the end of "strings", never overwriting existing ones;
  * refuse to run if the file still holds merge conflict markers.

Tool and layer-mask entries are keyed as full "Tool › Name" / "Layer › …" strings
rather than bare names, because the bare names collide with keys used elsewhere:
"Type" is already "类型" (correct for BrushControls' "kind" picker) but the type
tool must read 文字, and "Line"/"Hand"/"Rectangle" have non-tool meanings too.
Composite keys are safe here because these entries are built in code, not joined
at runtime from already-localised menu items.
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
    # --- Palette chrome: SwiftUI literals, localised via LocalizedStringKey ---
    "Search commands and tools": "搜索命令与工具",
    "No commands match": "没有匹配的命令",
    # --- The palette's own menu item (CompositorApp.swift), and its name in the Keyboard Shortcuts list ---
    "Search Commands…": "搜索命令…",
    "Search Commands": "搜索命令",

    # --- Tools: "Tool › <name>" as CommandPalette.swift builds them ---
    "Tool › Move / Transform": "工具 › 移动/变换",
    "Tool › Rectangular Marquee": "工具 › 矩形选框",
    "Tool › Elliptical Marquee": "工具 › 椭圆选框",
    "Tool › Lasso": "工具 › 套索",
    "Tool › Polygonal Lasso": "工具 › 多边形套索",
    "Tool › Magic Wand": "工具 › 魔棒",
    "Tool › Object Selection": "工具 › 对象选择",
    "Tool › Crop": "工具 › 裁剪",
    "Tool › Brush": "工具 › 画笔",
    "Tool › Eraser": "工具 › 橡皮擦",
    "Tool › Spot Healing Brush": "工具 › 污点修复画笔",
    "Tool › Clone Stamp": "工具 › 仿制图章",
    "Tool › Liquify": "工具 › 液化",
    "Tool › Blur": "工具 › 模糊",
    "Tool › Smudge": "工具 › 涂抹",
    "Tool › Gradient": "工具 › 渐变",
    "Tool › Rectangle": "工具 › 矩形",
    "Tool › Ellipse": "工具 › 椭圆",
    "Tool › Line": "工具 › 直线",
    "Tool › Type": "工具 › 文字",
    "Tool › Eyedropper": "工具 › 吸管",
    "Tool › Hand": "工具 › 抓手",
    "Tool › Zoom": "工具 › 缩放",

    # --- Layer mask commands (the Layers panel's mask button) ---
    "Layer › Add Layer Mask": "图层 › 添加图层蒙版",
    "Layer › Add Layer Mask from Selection": "图层 › 从选区添加图层蒙版",
    "Layer › Add Layer Mask Hiding Selection": "图层 › 添加隐藏选区的图层蒙版",
    "Layer › Add Layer Mask (Hide All)": "图层 › 添加图层蒙版 (全部隐藏)",
}


def main() -> int:
    with open(CATALOG, "rb") as handle:
        original = handle.read()

    text = original.decode("utf-8")
    for marker in ("<<<<<<<", "=======", ">>>>>>>"):
        if marker in text:
            print(f"ABORT: {CATALOG} still contains conflict marker {marker!r}", file=sys.stderr)
            return 1

    catalog = json.loads(text)

    # Prove the round-trip is byte-identical before we change anything.
    probe = json.dumps(catalog, indent=2, ensure_ascii=False)
    if probe.encode("utf-8") != original:
        print("ABORT: re-serialising the catalog does not reproduce the original bytes.",
              file=sys.stderr)
        print("Refusing to rewrite the file; inspect its formatting first.", file=sys.stderr)
        return 1

    strings = catalog["strings"]
    added, skipped = [], []
    for key, value in TRANSLATIONS.items():
        if key in strings:
            skipped.append(key)
            continue
        strings[key] = {
            "localizations": {
                "zh-Hans": {"stringUnit": {"state": "translated", "value": value}}
            }
        }
        added.append(key)

    if not added:
        print("Nothing to add (all keys already present).")
        return 0

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"Localizable.xcstrings.{stamp}.bak")
    shutil.copy2(CATALOG, backup)

    with open(CATALOG, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(catalog, indent=2, ensure_ascii=False))

    print(f"backup: {backup}")
    print(f"added {len(added)} keys, skipped {len(skipped)} already present")
    for key in added:
        print(f"  + {key}  ->  {TRANSLATIONS[key]}")
    for key in skipped:
        print(f"  = (already present) {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
