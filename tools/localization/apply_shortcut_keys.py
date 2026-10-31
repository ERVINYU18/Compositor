#!/usr/bin/env python3
"""Add zh-Hans translations for the Keyboard Shortcuts panel.

The panel stores each shortcut's identity as "group:title" in UserDefaults, so the English
title must stay the canonical key; only the rendered text is translated. Every key here is
verified to exist in the source (as a literal, or via the template that composes it) before
anything is written.
"""
import json
import os
import shutil
import sys

import os as _os
REPO = _os.environ.get("COMPOSITOR_CN_REPO") or _os.path.abspath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(REPO, "Compositor/UI/KeyboardShortcuts.swift")
CATALOG = os.path.join(REPO, "Compositor/Localizable.xcstrings")
BACKUP = "/Users/yi/Desktop/AI/DSH/Compositor CN/01-merge-scene-evidence/Localizable.xcstrings.before-shortcuts"

# literal titles: key -> translation (the literal must appear in the source)
LITERAL = {
    "Apply current canvas operation": "应用当前画布操作",
    "Blur / Smudge / Liquify": "模糊／涂抹／液化",
    "Brush tool": "画笔工具",
    "Cancel current canvas operation": "取消当前画布操作",
    "Crop tool": "裁剪工具",
    "Cycle shape kind": "循环切换形状类型",
    "Cycle tool mode": "循环切换工具模式",
    "Decrease brush hardness": "减小画笔硬度",
    "Decrease brush size": "减小画笔大小",
    "Decrease leading": "减小行距",
    "Decrease tracking": "减小字距",
    "Delete selection / layer / effect / lasso point": "删除选区／图层／效果／套索点",
    "Duplicate / Layer via Copy": "复制／通过拷贝的图层",
    "Eyedropper tool": "吸管工具",
    "Fill with Background": "用背景色填充",
    "Fill with Foreground": "用前景色填充",
    "Finish editing text": "完成文本编辑",
    "Gradient tool": "渐变工具",
    "Hand tool": "抓手工具",
    "Increase brush hardness": "增大画笔硬度",
    "Increase brush size": "增大画笔大小",
    "Increase leading": "增大行距",
    "Increase tracking": "增大字距",
    "Inverse Selection": "反选",
    "Invert Pixels / Mask": "反相像素／蒙版",
    "Lasso / cycle mode": "套索／循环切换模式",
    "Marquee / cycle shape": "选框／循环切换形状",
    "Move / Transform tool": "移动／变换工具",
    "Next blend mode": "下一个混合模式",
    "Previous blend mode": "上一个混合模式",
    "Reset colors": "重置颜色",
    "Save As": "存储为",
    "Select Subject": "选择主体",
    "Select tool": "选择工具",
    "Shape tool": "形状工具",
    "Swap foreground/background": "交换前景色／背景色",
    "Temporary Hand tool (hold)": "临时抓手工具（按住）",
    "Toggle Clipping Mask": "切换剪贴蒙版",
    "Toggle Levels preview": "切换色阶预览",
    "Transform Layer / Selection": "变换图层／选区",
    "Type tool": "文字工具",
    "Zoom tool": "缩放工具",
}

# group headers
GROUPS = {
    "Menus": "菜单",
    "Canvas & Layers": "画布与图层",
    "Text Editing": "文本编辑",
}

# panel validation messages
MESSAGES = {
    "Choose a single key with optional modifiers.": "请选择一个按键，可附带修饰键。",
    "Text-editing shortcuts need Command, Option, or Control so they do not replace normal typing.":
        "文本编辑快捷键需要 Command、Option 或 Control，以免取代正常的文字输入。",
    "%@ is reserved by macOS.": "%@ 已被 macOS 保留。",
    "%@ is assigned to both %@ and %@.": "%@ 同时分配给了 %@ 和 %@。",
}

DIRECTION_ZH = {"Left": "向左", "Right": "向右", "Up": "向上", "Down": "向下"}
BY10 = {
    "Decrease tracking": "减小字距",
    "Increase tracking": "增大字距",
    "Decrease leading": "减小行距",
    "Increase leading": "增大行距",
}


def build():
    """Return {key: (translation, verify_substring)}."""
    out = {}
    for k, v in LITERAL.items():
        out[k] = (v, f'"{k}"')
    for k, v in GROUPS.items():
        out[k] = (v, f'"{k}"')
    for k, v in MESSAGES.items():
        out[k] = (v, f'localizedString("{k}")')

    # digit-composed titles
    for d in range(10):
        out[f"Opacity digit {d} (type two for exact %)"] = (
            f"不透明度数字 {d}（连按两次输入精确百分比）",
            'entry("Opacity digit \\(digit) (type two for exact %)',
        )
    # direction-composed titles
    for direction, zh in DIRECTION_ZH.items():
        for n in (1, 10):
            out[f"Nudge {direction} {n} px"] = (f"{zh}微移 {n} 像素", 'entry("Nudge \\(direction) 1 px"')
            out[f"Move selected pixels {direction} {n} px"] = (
                f"{zh}移动所选像素 {n} 像素",
                'entry("Move selected pixels \\(direction) 1 px"',
            )
    # "by 10" composed titles
    for base, zh in BY10.items():
        out[base + " by 10"] = (f"{zh} 10", 'title + " by 10"')
    return out


def main():
    entries = build()
    src = open(SRC, encoding="utf-8").read()

    problems = [f"NOT IN SOURCE: {key!r} (expected {verify!r})"
                for key, (_v, verify) in entries.items() if verify not in src]
    if problems:
        print("ABORT: source verification failed")
        for p in problems:
            print("   ", p)
        return 1
    print(f"source verification : {len(entries)}/{len(entries)} keys accounted for")

    raw = open(CATALOG, encoding="utf-8").read()
    doc = json.loads(raw)
    if json.dumps(doc, indent=2, ensure_ascii=False) + "\n" != raw:
        print("ABORT: serializer would not round-trip byte-identically")
        return 1

    shutil.copy2(CATALOG, BACKUP)
    strings = doc["strings"]
    added, already = [], []
    for key, (value, _verify) in entries.items():
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
