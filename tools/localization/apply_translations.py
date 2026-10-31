#!/usr/bin/env python3
"""Add zh-Hans translations for UI strings missing from Compositor/Localizable.xcstrings.

Serialization matches the existing file byte-for-byte on a no-op round trip:
json.dumps(..., indent=2, ensure_ascii=False) + "\n", preserving key order.
New keys are appended to the end of "strings" so the diff is pure addition.
"""
import json
import shutil
import sys

CATALOG = "/Users/yi/Desktop/Compositor-CN/Compositor/Localizable.xcstrings"
BACKUP = "/Users/yi/Desktop/AI/DSH/Compositor CN/01-merge-scene-evidence/Localizable.xcstrings.before"

TRANSLATIONS = {
    "%@ Selection": "%@选区",
    "Applies generic profile strength when camera metadata is not available.":
        "相机元数据不可用时，应用通用配置文件强度。",
    "Auto balances the average color. Custom follows Temperature and Tint.":
        "自动会平衡平均颜色。自定义则依据色温和色调。",
    "Blend the chosen color into the edges while keeping the center unchanged":
        "将所选颜色融入边缘，同时保持中心不变",
    "Choose a custom grid color": "选择自定义网格颜色",
    "Choose the vignette color": "选择晕影颜色",
    "Chooses how strongly the calibration sliders below are applied. Version 6 is the current default.":
        "决定下方校准滑块的强度。版本 6 为当前默认值。",
    "Clear Menu": "清除菜单",
    "Click a pixel that should be neutral.": "点按应为中性色的像素。",
    "Click a purple or green fringe to set its hue range.": "点按紫色或绿色边缘以设定其色相范围。",
    "Click the picture to save a color. Up to eight colors.": "点按图片以保存颜色。最多八种颜色。",
    "Color Picker (%@ Color)": "取色器（%@颜色）",
    "Color Picker (Text Color)": "取色器（文字颜色）",
    "Color for the added canvas": "新增画布的颜色",
    "Color that fills transparent areas": "填充透明区域的颜色",
    "Crops empty edges after the transform and fits the result back into the frame.":
        "变换后裁掉空白边缘，并将结果重新适合到画面中。",
    "Delete %@": "删除%@",
    "Diffusion is soft and wide, Bloom is tighter, and Halation is a red fringe.":
        "扩散柔和而宽广，泛光更集中，光晕则呈红色边缘。",
    "Dims the picture outside this color's range. It is not kept when you press OK.":
        "使此颜色范围之外的画面变暗。按下“好”后不会保留。",
    "Drag a color in the picture. Nearby color families move together.":
        "在图片中拖动颜色。相邻的色系会一起移动。",
    "Drag inside the wheel. Angle sets hue, distance sets saturation.":
        "在色轮内拖动。角度决定色相，距离决定饱和度。",
    "Drag or scroll to move around; double-click switches between Fit and 100%":
        "拖动或滚动以移动视图；双击可在“适合”与 100% 之间切换",
    "Drag to set hue and saturation. Double-click to reset this wheel.":
        "拖动以设定色相和饱和度。双击可重置此色轮。",
    "Draw two or more lines on the preview that should be level or vertical.":
        "在预览上绘制两条或更多应保持水平或垂直的线。",
    "End of the hue range, in degrees.": "色相范围的结束角度（度）。",
    "Grid Settings…": "网格设置…",
    "HSL lists every color. Color edits one family. Point Color adjusts a color you pick.":
        "HSL 列出所有颜色。“颜色”用于编辑某一个色系。“点颜色”调整你选取的颜色。",
    "Highlight Priority protects bright edges. Color Priority also reduces color. Paint Overlay covers the edges evenly.":
        "高光优先保护明亮边缘。颜色优先还会降低色彩。绘制叠加则均匀覆盖边缘。",
    "How far a color may be from the picked ones and still be selected":
        "颜色距离所选颜色多远仍会被选中",
    "Hue and saturation of this wheel.": "此色轮的色相和饱和度。",
    "Hue shifts the color, Saturation its strength, and Luminance its brightness.":
        "色相改变颜色，饱和度改变强度，明度改变明暗。",
    "Input and output of the selected curve point.": "所选曲线点的输入和输出。",
    "Lock aspect ratio. Hold Shift while dragging a handle to turn it the other way.":
        "锁定宽高比。拖动手柄时按住 Shift 可反转锁定状态。",
    "Off leaves the picture as it is. Guided straightens from lines you draw on the picture.":
        "关闭会保持画面不变。参考线会根据你在画面上绘制的线进行校正。",
    "Open Recent": "最近使用",
    "Parametric lifts tonal regions. Point places anchors on the curve.":
        "参数会调整各个影调区域。点会在曲线上放置锚点。",
    "Perspective allows stronger keystone. Rectilinear keeps the warp gentler.":
        "透视允许更强的梯形校正。直线投影则使变形更平缓。",
    "Protect bright areas near the edge": "保护边缘附近的明亮区域",
    "Pulls red and blue fringes apart toward the center to reduce color edging.":
        "将红色和蓝色边缘向中心拉开，以减少色边。",
    "RGB changes brightness. Red, green, and blue also shift the color.":
        "RGB 改变亮度。红、绿、蓝还会改变颜色。",
    "Red, green, and blue of the pixel under the pointer.":
        "指针所指像素的红、绿、蓝数值。",
    "Remove every guide line.": "移除所有参考线。",
    "Replaces this curve with a straight line or a contrast curve.":
        "将此曲线替换为直线或对比度曲线。",
    "Select everything except those colors, such as all but a green screen":
        "选择这些颜色之外的所有内容，例如除绿幕以外的全部",
    "Select layer mask; Option-click to view it alone; Shift-click to enable/disable; Cmd-click to select its black areas (Cmd-Shift adds, Cmd-Option subtracts)":
        "选择图层蒙版；按住 Option 点击可单独查看；按住 Shift 点击可启用或停用；按住 Command 点击可选择黑色区域（Command-Shift 添加，Command-Option 减去）",
    "Select layers by clicking the canvas. Hold Command to turn it the other way while you click.":
        "点按画布选择图层。按住 Command 点按可反向选择。",
    "Select this picked color.": "选择此已拾取的颜色。",
    "Show the image again (or Option-click the mask thumbnail)":
        "重新显示图像（或按住 Option 点按蒙版缩览图）",
    "Show the whole image (⌘0)": "显示整个图像（⌘0）",
    "Start of the hue range, in degrees.": "色相范围的起始角度（度）。",
    "The brush trails the pointer on a string this long, so a shaky hand still draws a smooth line":
        "画笔会以这样长度的“绳”跟随指针，因此手抖也能画出平滑的线条",
    "The height of each line of characters": "每行字符的高度",
    "Three-Way shows shadows, midtones, and highlights. The other choices show one wheel.":
        "三向显示阴影、中间调和高光。其他选项只显示一个色轮。",
    "Ungroup Layers": "取消图层编组",
}


def main():
    raw = open(CATALOG, encoding="utf-8").read()
    doc = json.loads(raw)
    strings = doc["strings"]

    # Safety: prove the round trip is byte-identical before mutating
    if json.dumps(doc, indent=2, ensure_ascii=False) + "\n" != raw:
        print("ABORT: serializer would not round-trip byte-identically")
        return 1

    shutil.copy2(CATALOG, BACKUP)

    added, skipped = [], []
    for key, value in TRANSLATIONS.items():
        if key in strings:
            skipped.append(key)
            continue
        strings[key] = {
            "localizations": {"zh-Hans": {"stringUnit": {"state": "translated", "value": value}}}
        }
        added.append(key)

    out = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    open(CATALOG, "w", encoding="utf-8").write(out)

    # Verify what we wrote
    check = json.load(open(CATALOG, encoding="utf-8"))
    bad = [
        k for k in added
        if not (((check["strings"][k].get("localizations") or {}).get("zh-Hans") or {})
                .get("stringUnit") or {}).get("value")
    ]
    print(f"planned            : {len(TRANSLATIONS)}")
    print(f"added              : {len(added)}")
    print(f"already present    : {len(skipped)} {skipped if skipped else ''}")
    print(f"total keys now     : {len(check['strings'])}")
    print(f"entries failing verify: {len(bad)} {bad if bad else ''}")
    print(f"re-serialization stable : {json.dumps(check, indent=2, ensure_ascii=False) + chr(10) == out}")
    return 0 if not bad and not skipped else 2


if __name__ == "__main__":
    sys.exit(main())
