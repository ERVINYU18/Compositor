#!/usr/bin/env python3
"""Add the zh-Hans entries upstream v1.4.10 needs to Localizable.xcstrings.

Same conventions as add_1_4_9_keys.py:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing ones;
  * refuse to run while merge conflict markers remain.

Sources for the 1.4.10 cycle:
  * 02-localization/audit_strings.py  (UI literals missing from the catalog)
  * reading the upstream diff by hand: the audit's sink regexes miss conditional
    help text, written as .help(condition ? "supported" : "unsupported"), which is
    how every one of the new Camera Raw rows states its tooltip.
  * the two import messages, which upstream extended with HEIF.
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
    # --- Camera Raw: noise reduction, lens correction, highlight recovery (new in 1.4.10) ---
    "Highlight Recovery": "高光恢复",
    "Smooths grain, at the cost of fine detail": "平滑噪点，代价是损失一部分细节",
    "Removes the lens's distortion and vignetting": "消除镜头的畸变与暗角",
    "This file has no lens profile": "此文件没有镜头配置文件",
    "Brings back detail in bright areas the camera partly clipped": "找回相机部分过曝区域里的细节",
    "Not available for this camera": "此相机不支持",

    # --- Gaussian Blur: preserve transparency (new in 1.4.10) ---
    "Preserve Transparency": "保留透明度",
    "Blur only the colors, keeping the layer's outline and transparency as they are":
        "只模糊颜色，图层的轮廓与透明区域保持原样",

    # --- Import: HEIF joins the list of readable formats (1.4.10) ---
    "Choose a JPEG, PNG, HEIC, HEIF, TIFF, WebP, Photoshop (PSD), or Photoshop Large Document (PSB) file.":
        "请选择 JPEG、PNG、HEIC、HEIF、TIFF、WebP、Photoshop (PSD) 或 Photoshop 大文档 (PSB) 文件。",
    "Some dropped items couldn’t be read. Drag JPEG, PNG, HEIC, HEIF, TIFF, WebP, or Photoshop (PSD) files from Finder.":
        "部分拖入的项目无法读取。请从访达拖入 JPEG、PNG、HEIC、HEIF、TIFF、WebP 或 Photoshop (PSD) 文件。",
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
