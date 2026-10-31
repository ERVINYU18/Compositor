#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.5.6 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 / add_1_4_10 / add_1_5_3 / add_1_5_5:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

Sources for the 1.5.6 cycle:
  * 02-localization/audit_strings.py  (23 UI literals missing from the catalog)
  * a wider sweep of every literal in Compositor/ that is not in the catalog,
    which also catches what the audit's sink regex misses: enum-backed labels
    (`LayerType.titleKey`), ternaries (`isPlaying ? "Pause" : "Play"`) and
    AppKit setters (`placeholderString`);
  * the official diff by hand: GIF import/export, the animation timeline, the
    Layers panel's search and type filter, and ToolRail's extraction.

Deliberately NOT translated:
  * "Generic CMYK Profile" / "Embedded CMYK Profile" — ColorSync profile names.
    `CMYK.generic` matches macOS's profile by that exact string, so translating
    it would silently break profile lookup.
  * GIFDelayMode's raw values ("Frame delay", "Same for all") — Codable
    storage values, never shown.
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
    # --- GIF export: the settings grid and its background swatch ---
    "Loop": "循环",
    "Forever": "永久",
    "Once": "一次",
    "Transparency": "透明度",
    "Keep transparent areas": "保留透明区域",
    "Frames": "帧数",
    "GIF keeps fully transparent or opaque pixels; soft edges use a 50% threshold.":
        "GIF 只保留完全透明或完全不透明的像素；柔和边缘按 50% 阈值处理。",
    "Up to 256 colors · sRGB": "最多 256 色 · sRGB",
    "1 frame · Still canvas": "1 帧 · 静态画布",
    "%@ frames": "%@ 帧",
    "Encoding frame %lld of %lld…": "正在编码第 %lld 帧，共 %lld 帧…",
    "Animation export supports up to %@ frames, %lld megapixels across all exported frames, "
    "and 512 MiB of encoded data. Reduce the export size or frame count.":
        "动画导出最多支持 %@ 帧、所有导出帧合计 %lld 百万像素，以及 512 MiB 的编码数据。"
        "请减小导出尺寸或减少帧数。",
    "The selected animation timeline is missing or invalid.": "所选动画时间轴缺失或无效。",

    # --- Export As: the animation preview button and the preview's own help ---
    "Play the animation preview.": "播放动画预览。",
    "Pause the animation preview.": "暂停动画预览。",
    "Play animation preview": "播放动画预览",
    "Pause animation preview": "暂停动画预览",
    "Enabled masks apply here, as on the canvas. Drag or scroll to move around; "
    "double-click switches between Fit and 100%.":
        "已启用的蒙版在此同样生效，与画布一致。拖动或滚动可移动视图；"
        "双击在「适合窗口」与 100% 之间切换。",

    # --- Export As: the format menu's help, now that GIF is one of the formats ---
    "Other formats: TIFF, PDF and GIF, EXR to keep light brighter than white, "
    "and Channel Pack for game textures":
        "其他格式：TIFF、PDF 和 GIF；EXR 可保留比白色更亮的光；通道包用于游戏贴图",
    "Other formats: TIFF, PDF and GIF, and Channel Pack for game textures":
        "其他格式：TIFF、PDF 和 GIF，以及用于游戏贴图的通道包",
    "What fills the %@ channel: a layer or group read as grayscale, or solid black or white":
        "填充 %@ 通道的内容：按灰度读取的图层或组，或纯黑、纯白",

    # --- Export As: the PDF page's size line (an old leak the sweep turned up) ---
    "%@ × %@ in at %lld DPI": "%@ × %@ 英寸，%lld DPI",

    # --- The animation timeline under the canvas ---
    "Play": "播放",
    "Pause": "暂停",
    "How long each frame shows": "每一帧显示多长时间",
    "Duplicate Frame": "复制帧",
    "Delete Frame": "删除帧",
    "Frame %lld": "第 %lld 帧",
    "%lld ms · %@ fps": "%lld 毫秒 · %@ fps",

    # --- GIF edits' history names, which the Edit and History menus show ---
    "Change GIF Delays": "更改 GIF 帧延迟",
    "Duplicate GIF Frame": "复制 GIF 帧",
    "Delete GIF Frame": "删除 GIF 帧",
    "Delete GIF Frames": "删除 GIF 帧",

    # --- Import and the project file ---
    "Choose a JPEG, PNG, GIF, HEIC, HEIF, TIFF, WebP, PDF, Photoshop (PSD), "
    "or Photoshop Large Document (PSB) file.":
        "请选择 JPEG、PNG、GIF、HEIC、HEIF、TIFF、WebP、PDF、Photoshop (PSD) "
        "或 Photoshop 大文档 (PSB) 文件。",
    "Some dropped items couldn’t be read. Drag JPEG, PNG, GIF, HEIC, HEIF, TIFF, WebP, PDF, "
    "or Photoshop (PSD) files from Finder.":
        "部分拖入的项目无法读取。请从访达拖入 JPEG、PNG、GIF、HEIC、HEIF、TIFF、WebP、PDF "
        "或 Photoshop (PSD) 文件。",
    "This animation has more than %@ frames, which exceeds the current timeline limit.":
        "此动画的帧数超过 %@，已超出当前时间轴上限。",
    "Couldn’t read GIF frame %lld: %@": "无法读取 GIF 第 %lld 帧：%@",
    "The copied GIFs exceed this project’s animation memory limit.":
        "复制的 GIF 超出了此项目的动画内存上限。",
    "This project uses format version %lld. This app supports versions %lld–%lld, 27, and %lld.":
        "此项目使用的格式版本为 %lld。本 App 支持版本 %lld–%lld、27 和 %lld。",

    # --- The Layers panel's title row: search and the type filter ---
    "Search layers by name": "按名称搜索图层",
    "Close the search": "关闭搜索",
    "Search layers": "搜索图层",
    "Close search": "关闭搜索",
    "Search Layers": "搜索图层",
    "Show only some kinds of layer": "只显示某几类图层",
    "Filter the layer list": "筛选图层列表",
    "Images": "图像",
    "Shapes": "形状",
    "Folders": "文件夹",
    "Adjustments": "调整",
    "Filter to image layers": "筛选图像图层",
    "Filter to shape layers": "筛选形状图层",
    "Filter to text layers": "筛选文字图层",
    "Filter to folder layers": "筛选文件夹图层",
    "Filter to adjustment layers": "筛选调整图层",
    "Filter to the selected layers": "筛选选中的图层",
    "No layers match the filter.": "没有图层符合筛选条件。",
    "Clear All": "全部清除",

    # --- The Layers panel's empty state ---
    "Create a canvas or import a file.": "新建画布或导入文件。",
    "Import a file or add a blank layer.": "导入文件或添加空白图层。",

    # --- The GIF layer's tag in the layer list ---
    "Animated GIF: select it to show its frames under the canvas":
        "动画 GIF：选中后可在画布下方显示其帧",

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
