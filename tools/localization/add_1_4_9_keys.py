#!/usr/bin/env python3
"""Add the zh-Hans entries upstream v1.4.9 needs to Localizable.xcstrings.

Same conventions as apply_translations.py / add_command_palette_translations.py:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing ones;
  * refuse to run while merge conflict markers remain.

Sources of this list, for the 1.4.9 cycle:
  * 02-localization/audit_strings.py  (UI literals missing from the catalog)
  * UpdaterCore.sh's scan_dynamic_english  (values shown through a variable, which
    SwiftUI does not look up: DitherColors' rawValue)
  * a per-file extraction of FilterSheet's control()/help()/swatch() literals,
    which the sink-based audit only partly reaches.
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
    # --- File > Export As… (new in 1.4.9; replaces the old JPEG-only sheet) ---
    "Export As": "导出为",
    "Export As…": "导出为…",
    "Format": "格式",
    "Page": "页面",
    "Export Background": "导出背景",
    "Width in pixels; the height follows, keeping the proportions": "宽度（像素）；高度按比例跟随",
    "Height in pixels; the width follows, keeping the proportions": "高度（像素）；宽度按比例跟随",
    "Scale the export: the document stays as it is": "缩放导出内容；文档本身不变",
    "Zoom in (⌘+), now %@. At 100%% each pixel of the export is one pixel of the screen":
        "放大（⌘+），当前 %@。100%% 时导出的每个像素正好对应屏幕上的一个像素",
    "Transparency kept · sRGB": "保留透明度 · sRGB",

    # --- Import: WebP joins the list of readable formats (1.4.9) ---
    "Importing…": "正在导入…",
    "Choose a JPEG, PNG, HEIC, TIFF, WebP, Photoshop (PSD), or Photoshop Large Document (PSB) file.":
        "请选择 JPEG、PNG、HEIC、TIFF、WebP、Photoshop (PSD) 或 Photoshop 大文档 (PSB) 文件。",
    "Some dropped items couldn’t be read. Drag JPEG, PNG, HEIC, TIFF, WebP, or Photoshop (PSD) files from Finder.":
        "部分拖入的项目无法读取。请从访达拖入 JPEG、PNG、HEIC、TIFF、WebP 或 Photoshop (PSD) 文件。",

    # --- Navigator, the canvas-corner minimap from 300% zoom ---
    "Navigator": "导航器",
    "Navigator (300% and above)": "导航器（300% 及以上）",

    # --- View menu items that were never in the catalog ---
    "Rotate Canvas 90° Clockwise": "顺时针旋转画布 90°",
    "Rotate Canvas 90° Counterclockwise": "逆时针旋转画布 90°",
    "Toggle Fullscreen": "切换全屏",

    # --- Layers panel ---
    "Add layer effect": "添加图层效果",

    # --- Filter > Scanlines (new filter in 1.4.9) ---
    "Scanlines": "扫描线",
    "Thickness": "粗细",
    "Threshold": "阈值",
    "Displace": "位移",
    "Smoothness": "平滑",
    "Black Level": "黑场",
    "Color Split": "颜色分离",
    "Darker or lighter before the lines are drawn": "绘制线条前先调暗或调亮画面",
    "Draw no line where the picture is darker than this, leaving the screen dark":
        "画面暗于此处时不画线，让屏幕保持暗色",
    "Break the lines into beads where the picture is darker than this, blending into solid lines where it's brighter":
        "画面暗于此处时线条断成点状，越亮越连成实线",
    "How much of the gap a bright line fills; dimmer parts draw it thinner":
        "亮线填充间隙的程度；越暗的地方线条越细",
    "How far the brightness is smoothed before it displaces the lines, from sharp ridges to rounded hills":
        "位移线条前对亮度做多大范围的平滑，从锐利的脊线到圆缓的丘陵",
    "Lift the lines where the picture is bright, or lower them when negative, so they swell into its shapes":
        "按画面亮度抬升线条，取负值时则下压，让线条随画面形状起伏",
    "How bright the lines are where the picture is black, so they show even over black":
        "画面为黑处线条的亮度，让它在纯黑上仍然可见",
    "Move the red and blue apart, for colored fringes on the lines":
        "分离红色与蓝色，在线条上形成彩色边缘",
    "Choose the screen's color": "选择屏幕颜色",
    "Choose the lines' color": "选择线条颜色",
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
