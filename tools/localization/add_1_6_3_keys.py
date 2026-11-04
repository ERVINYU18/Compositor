#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.6.3 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 / 1_4_10 / 1_5_3 / 1_5_5 / 1_5_6 / 1_5_7 / 1_5_8 /
1_5_9 / 1_5_11 / 1_5_12:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

What 1.6.3 needs (56 commits, 64 files, +3873/-306). This round carries
v1.6.0, v1.6.1 and v1.6.2 as well; none was merged separately.

  * Volumetric Light (体积光): a destructive filter, not an adjustment layer.
    New labels Haze / Depth Contrast / Intensity / Shafts / Keep Subject Clear,
    the canvas hint, the light's colour button, "Getting depth…" and
    "Extract Depth", plus nine .help() strings. Its settings live in
    FilterSettings, not FilterLayerSettings, so they are not saved and the
    project format does not move for it.
  * Reduce Noise (降噪): a filter and, from format 21, an adjustment layer.
    "Strength" already exists (强度); "Preserve Details" and "Color Noise" are
    new, with three .help() strings.
  * View menu: "Show Extras" (⌘H outside the Move tool) and "Distances".
  * Layers panel: the footer's new filter menu needs "New filter layer";
    "New adjustment layer" and "Add layer effect" already exist.
  * Layer export: save/open panel titles, folder prompt, Replace/Export
    buttons, the two replace warnings and the two "nothing to export" lines.
  * Status bar: the selection's size, "Selection %lld × %lld px".
  * Visibility on several selected layers: "Show Layers" / "Hide Layers".
    Singular "Show Layer" / "Hide Layer" already exist.

Deliberately NOT translated (checked this round):
  * Core Image filter names and Metal function names in VolumetricLight.swift,
    MetalVolumetricLight.swift, GPUReduceNoise.swift, MetalNonlocalMeans.swift
    ("CIColorMatrix", "inputRVector", "volumetricBeams"…); none reaches the UI.
  * DepthModel.swift's release file names and SHA-256 fingerprints.
  * SF Symbol names in LayersPanel.swift ("circle.lefthalf.filled", "sparkles").
  * ProjectController.fileName's "Layer" fallback: it is a file name, not UI;
    the exported file keeps that name.
  * Test-only strings in CompositorTests, including file-name expectations.
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
    # --- Filter menu + sheet titles ---
    "Reduce Noise": "降噪",
    "Volumetric Light": "体积光",
    # --- Reduce Noise controls ---
    "Preserve Details": "保留细节",
    "Color Noise": "彩色噪点",
    "How much grain is smoothed from the picture's brightness":
        "按画面亮度平滑多少颗粒",
    "How much fine texture and edges are kept while the grain is smoothed":
        "平滑颗粒时保留多少细纹理与边缘",
    "How much colored speckle is smoothed into the colors around it":
        "把多少彩色斑点平滑到周围的颜色中",
    # --- Volumetric Light controls ---
    "Haze": "雾气",
    "Depth Contrast": "深度对比",
    "Intensity": "强度",
    "Shafts": "光束",
    "Keep Subject Clear": "保持主体清晰",
    "Click or drag on the canvas to move the light":
        "在画布上单击或拖动以移动灯光",
    "Choose the light's color": "选择灯光的颜色",
    "Getting depth…": "正在获取深度…",
    "Extract Depth": "提取深度",
    "Close the filter and add the depth the haze goes by as a new layer: white is near, black is far":
        "关闭滤镜，并将雾气所依据的深度作为新图层添加：白色表示近，黑色表示远",
    "How thick the air is: haze lit by the light, thinner in front of the subject":
        "空气的浓稠程度：被灯光照亮的雾气更浓，主体前方更薄",
    "How far into the scene the haze begins: low reaches up to the camera, high leaves all but the farthest parts clear":
        "雾气从场景多远处开始：数值低时一直延伸到相机前，数值高时只保留最远处的部分",
    "Spread out depths bunched together, such as a distant city, so the haze builds through them in steps; 0 keeps the depth as the model sees it":
        "把挤在一起的深度（例如远处的城市）拉开，让雾气分层累积；0 表示保持模型看到的原始深度",
    "How big the light is": "灯光的大小",
    "How bright the beams are": "光束的亮度",
    "How far from the light the beams reach": "光束从灯光向外延伸的距离",
    "How much the beams break up into separate shafts": "光束分散成独立光柱的程度",
    "Keep the subject clear of the haze; off, it's hazed by its own distance, so a figure far off is misted":
        "让主体不受雾气影响；关闭后主体会按自身距离被雾化，远处的人物会显得朦胧",
    # --- View menu + status bar ---
    "Show Extras": "显示附加内容",
    "Distances": "距离",
    "Selection %lld × %lld px": "选区 %1$lld × %2$lld 像素",
    # --- Layers panel / visibility on several layers ---
    "New filter layer": "新建滤镜图层",
    "Show Layers": "显示图层",
    "Hide Layers": "隐藏图层",
    # --- Layer export ---
    "Export Layer as PNG": "导出图层为 PNG",
    "Export %lld Layers as PNGs": "导出 %lld 个图层为 PNG",
    "Choose a folder for the layers’ PNGs.": "选择用于存放图层 PNG 的文件夹。",
    "Export": "导出",
    "Replace": "替换",
    "“%@” already exists. Replace it?": "“%@”已存在。要替换吗？",
    "%lld of these files already exist in “%@”. Replace them?":
        "其中 %lld 个文件已存在于“%@”中。要替换它们吗？",
    "“%@” has nothing to export": "“%@”没有可导出的内容",
    "%lld layers have nothing to export": "有 %lld 个图层没有可导出的内容",
    "A layer with no visible pixels, such as an adjustment layer, isn’t saved as a PNG.":
        "没有可见像素的图层（例如调整图层）不会保存为 PNG。",
    "Couldn’t export layers": "无法导出图层",
    "Export Layer as PNG…": "导出图层为 PNG…",
    "Export Layers as PNGs…": "导出多个图层为 PNG…",
}

# Nothing became obsolete this round. If a later round retires one of these
# keys, add it here with the snippet still_referenced() should look for; the
# script will only delete it once no Swift source spells it.
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
