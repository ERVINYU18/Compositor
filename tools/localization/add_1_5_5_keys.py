#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.5.5 needs to Localizable.xcstrings.

Same conventions as add_1_4_9_keys.py / add_1_4_10_keys.py:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet (1.5.5 brought
    an empty key upstream);
  * refuse to run while merge conflict markers remain.

Sources for the 1.5.5 cycle:
  * 02-localization/audit_strings.py  (21 UI literals missing from the catalog)
  * the official diff by hand: PDF import, Channel Pack export, the rewritten
    font picker, pen-pressure brushes, and the dispersion filter.
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
    # --- Import: PDF joins the readable formats, and a locked PDF has its own error ---
    "Choose a JPEG, PNG, HEIC, HEIF, TIFF, WebP, PDF, Photoshop (PSD), or Photoshop Large Document (PSB) file.":
        "请选择 JPEG、PNG、HEIC、HEIF、TIFF、WebP、PDF、Photoshop (PSD) 或 Photoshop 大文档 (PSB) 文件。",
    "This PDF is password-protected. Save an unlocked copy, then import that.":
        "此 PDF 已加密。请先另存一份未加密的副本，再导入该副本。",
    "Some dropped items couldn’t be read. Drag JPEG, PNG, HEIC, HEIF, TIFF, WebP, PDF, or Photoshop (PSD) files from Finder.":
        "部分拖入的项目无法读取。请从访达拖入 JPEG、PNG、HEIC、HEIF、TIFF、WebP、PDF 或 Photoshop (PSD) 文件。",

    # --- Export As: Channel Pack for game textures ---
    "Each channel from a layer, read as grayscale · PNG":
        "每个通道取自一个图层，按灰度读取 · PNG",
    "Other formats: TIFF and PDF, EXR to keep light brighter than white, and Channel Pack for game textures":
        "其他格式：TIFF 和 PDF；EXR 可保留比白色更亮的光；通道包用于游戏贴图",
    "Other formats: TIFF and PDF, and Channel Pack for game textures":
        "其他格式：TIFF 和 PDF，以及用于游戏贴图的通道包",

    # --- Filter: dispersion (Color Split) and channel split ---
    "Which way the colors spread": "颜色扩散的方向",
    "How far the colors spread apart, red one way and blue the other":
        "颜色分开的距离：红向一侧，蓝向另一侧",
    "Smear the split into streaks along its direction":
        "沿分离方向把颜色涂抹成条痕",
    "Linear splits along one direction; Radial splits outwards from a center, sharp there":
        "线性：沿一个方向分离；径向：从中心向外分离，中心保持锐利",
    "Click or drag on the canvas to move the center":
        "在画布上点按或拖动可移动中心",
    "Split to Layers": "拆分为图层",
    "Split the layer's original channels into four grayscale layers, Red, Green, Blue and Alpha, "
    "for Export As › Channel Pack. Color under fully transparent pixels can't be recovered":
        "把图层的原始通道拆成四个灰度图层（红、绿、蓝、Alpha），供「导出为 › 通道包」使用。"
        "完全透明像素下方的颜色无法恢复。",

    # --- Brush: pen pressure ---
    "Pen pressure sets the size: a light touch paints a thinner line":
        "压感控制粗细：落笔越轻线条越细",
    "Pen pressure sets the opacity: a light touch paints fainter, up to the brush’s Opacity":
        "压感控制不透明度：落笔越轻颜色越淡，上限为画笔的不透明度",
    "Pressure for size": "压感控制粗细",
    "Pressure for opacity": "压感控制不透明度",

    # --- Shape: stroke style ---
    "Solid, dashed or dotted; dashes grow with the line's width":
        "实线、虚线或点线；虚线长度随线宽增加",
    "How the line's ends, and each of its dashes and dots, are finished":
        "线条两端以及每一段虚线、每一个点的收尾方式",
    "Cap": "端点",

    # --- Menu ---
    "Import…": "导入…",

    # --- Rewritten font picker: the list panel's own AppKit strings ---
    "Search Fonts": "搜索字体",
    "Clear search": "清除搜索",

    # --- Names the history menu and the export format list show ---
    "Split Channels": "拆分通道",
    "Channel Pack": "通道包",

    # --- Upstream ships an empty key; keep the count of keys lacking zh-Hans at zero ---
    "": "",
}


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

    if not added and not filled:
        print("Nothing to add (all keys already present with zh-Hans).")
        return 0

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"Localizable.xcstrings.{stamp}.bak")
    shutil.copy2(CATALOG, backup)

    with open(CATALOG, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(catalog, indent=2, ensure_ascii=False))

    print(f"backup: {backup}")
    print(f"added {len(added)} keys, filled {len(filled)} empty ones, skipped {len(skipped)}")
    for key in added:
        print(f"  + {key[:70]}  ->  {TRANSLATIONS[key][:40]}")
    for key in filled:
        print(f"  ~ (filled zh-Hans) {key[:70]}")
    for key in skipped:
        print(f"  = (already translated) {key[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
