#!/usr/bin/env python3
"""Add zh-Hans translations for merge-introduced UI strings found in the 1.4.1 adaptation.

Every key is verified to exist verbatim in the named source file before it is written,
so a transcription slip cannot silently create an orphan catalog entry.
"""
import json
import os
import shutil
import sys

import os as _os
REPO = _os.environ.get("COMPOSITOR_CN_REPO") or _os.path.abspath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
CATALOG = os.path.join(REPO, "Compositor/Localizable.xcstrings")
BACKUP = "/Users/yi/Desktop/AI/DSH/Compositor CN/01-merge-scene-evidence/Localizable.xcstrings.before-round2"

# key -> (translation, source file the key must appear in)
ENTRIES = {
    "Add layer mask (Option-click for a black mask)":
        ("添加图层蒙版（按住 Option 点击可添加黑色蒙版）", "Compositor/UI/LayerMaskMenu.swift"),
    "Add layer mask revealing the selection (Option-click to hide it)":
        ("添加显示选区的图层蒙版（按住 Option 点击可改为隐藏选区）", "Compositor/UI/LayerMaskMenu.swift"),
    "Layer Mask": ("图层蒙版", "Compositor/UI/LayerMaskMenu.swift"),
    "Show mask alone": ("单独显示蒙版", "Compositor/UI/NativeLayerList.swift"),
    "Reveal Selection": ("显示选区", "Compositor/Document/LayerMask.swift"),
    "Hide Selection": ("隐藏选区", "Compositor/Document/LayerMask.swift"),
    "1 more tab": ("还有 1 个标签页", "Compositor/UI/ProjectTabLayout.swift"),
    "%lld more tabs": ("还有 %lld 个标签页", "Compositor/UI/ProjectTabLayout.swift"),
    "Several layers are selected. Select just one to paint on it.":
        ("已选择多个图层。请只选择一个图层再绘画。", "Compositor/Document/EditorSession+Brush.swift"),
    "“%@” is a folder, which has no pixels of its own. Paint on a layer inside it, or on the folder’s mask.":
        ("“%@”是文件夹，本身没有像素。请在其内部的图层上绘画，或在该文件夹的蒙版上绘画。",
         "Compositor/Document/EditorSession+Brush.swift"),
    "“%@” is hidden, or inside a hidden folder. Show it to paint on it.":
        ("“%@”已隐藏，或位于已隐藏的文件夹中。请先显示它再绘画。",
         "Compositor/Document/EditorSession+Brush.swift"),
    "The layer mask is turned off. Shift-click its thumbnail to turn it on, then paint.":
        ("图层蒙版已停用。按住 Shift 点击其缩览图启用后即可绘画。",
         "Compositor/Document/EditorSession+Brush.swift"),
    "“%@” is an adjustment layer, with no pixels to paint. Paint on its mask instead.":
        ("“%@”是调整图层，没有可绘画的像素。请改为在其蒙版上绘画。",
         "Compositor/Document/EditorSession+Brush.swift"),
    "Nothing is selected, so there’s nowhere to paint. Choose Select › Deselect (⌘D) to paint anywhere.":
        ("当前没有选区，因此无处可绘画。请选择“选择”›“取消选择”（⌘D）后随处绘画。",
         "Compositor/Document/EditorSession+Brush.swift"),
    "Smudge and Liquify work on a layer's pixels, not its mask.":
        ("涂抹和液化作用于图层的像素，而不是其蒙版。", "Compositor/Document/SmudgeLiquify.swift"),
}


def main():
    raw = open(CATALOG, encoding="utf-8").read()
    doc = json.loads(raw)
    if json.dumps(doc, indent=2, ensure_ascii=False) + "\n" != raw:
        print("ABORT: serializer would not round-trip byte-identically")
        return 1

    # Verify every key exists verbatim in its source file
    problems = []
    for key, (_value, rel) in ENTRIES.items():
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            problems.append(f"missing file {rel}")
            continue
        if key not in open(path, encoding="utf-8").read():
            problems.append(f"KEY NOT IN SOURCE {rel}: {key!r}")
    if problems:
        print("ABORT: source verification failed")
        for p in problems:
            print("   ", p)
        return 1
    print(f"source verification : {len(ENTRIES)}/{len(ENTRIES)} keys found verbatim")

    shutil.copy2(CATALOG, BACKUP)

    strings = doc["strings"]
    added, already = [], []
    for key, (value, _rel) in ENTRIES.items():
        if key in strings:
            already.append(key)
            continue
        strings[key] = {
            "localizations": {"zh-Hans": {"stringUnit": {"state": "translated", "value": value}}}
        }
        added.append(key)

    out = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    open(CATALOG, "w", encoding="utf-8").write(out)

    check = json.load(open(CATALOG, encoding="utf-8"))
    bad = [k for k in added
           if not (((check["strings"][k].get("localizations") or {}).get("zh-Hans") or {})
                   .get("stringUnit") or {}).get("value")]
    print(f"added               : {len(added)}")
    print(f"already present     : {len(already)} {already if already else ''}")
    print(f"total keys now      : {len(check['strings'])}")
    print(f"failing verify      : {len(bad)} {bad if bad else ''}")
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main())
