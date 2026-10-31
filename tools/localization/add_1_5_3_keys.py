#!/usr/bin/env python3
"""Add the zh-Hans entries the v1.5.3 merge needs to Localizable.xcstrings.

Same conventions as add_1_4_10_keys.py / add_1_4_9_keys.py:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing ones;
  * refuse to run while merge conflict markers remain.

Sources for the 1.5.3 cycle:
  * 02-localization/audit-output-1.5.3.txt  (sink literals missing from the catalog)
  * 02-localization/sweep-repo-1.5.3.txt    (whole-repo sweep for interpolated
    strings, conditional help text and runtime-chosen keys the audit's regexes miss)
  * manual reading of every display path the sweeps could not classify
    (AppKit tooltips, NSCursor accessibility descriptions, NSWindow titles,
    verbatim Text, history-action names and PSD import notes).

Deliberate non-entries (documented in the conflict-resolution notes):
  * generated layer-name data: "Layer N", "Folder N", "<Shape> N" (upstream tests
    assert these English names);
  * internal scratch names that are never shown: "Tip", "Adjustment input",
    "CMYK Profiles" (folder), "QuickLook" (package folder), "Dropped" (temp file),
    the ICC profile names "Embedded/Generic CMYK Profile" (data, matched by name);
  * device preset titles: "4K", "1440p", "1080p", "iPhone 18 Pro (Max)",
    "MacBook Pro 14\\"/16\\"", "Studio Display" (product / format tokens);
  * format rawValues: PNG / JPEG / TIFF / PDF / EXR, "Helvetica", "Text" (text
    content default), PSD tag keys, Core Image filter identifiers;
  * the dormant UpdateDriver strings (Sparkle path is never started in CN builds).
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
    # --- Top-level menus and CMYK proofing (CompositorApp, LayerMaskMenu) ---
    "CMYK": "CMYK",
    "Proof Colors": "校样颜色",
    "CMYK Proof Colors": "CMYK 校样颜色",
    "Gamut Warning": "色域警告",
    "CMYK Gamut Warning": "CMYK 色域警告",
    "Profile": "配置文件",
    "Load Profile…": "载入配置文件…",
    "Last Filter": "上次滤镜",
    "Last Filter: %@": "上次滤镜：%@",
    "Choose a CMYK ICC profile, such as the one your printer gave you":
        "选择 CMYK ICC 配置文件，例如打印机随附的那一份",
    "Hide the gamut warning": "隐藏色域警告",
    "Stop marking colors the profile can't print": "停止标记配置文件无法打印的颜色",
    "Stop proofing": "停止校样",
    "Show the document's own colors again": "重新显示文档自身的颜色",
    "CMYK Proof": "CMYK 校样",

    # --- Export and its panels (ExportAsSheet, ProjectController) ---
    "Export As": "导出为",
    "Export %@": "导出 %@",
    "Couldn’t export": "无法导出",
    "Depth": "深度",
    "16 bits per channel": "每通道 16 位",
    "Keep the 16-bit layers' full precision, in a file about twice the size":
        "保留 16 位图层的完整精度，文件大小约两倍",
    "Use a CMYK ICC profile, such as the one your printer gave you":
        "使用 CMYK ICC 配置文件，例如打印机随附的那一份",
    "Brighter than white kept · Transparency kept": "保留比白色更亮的光 · 保留透明度",
    "CMYK writes a printer's inks through the profile in View › CMYK › Profile":
        "CMYK 通过「显示 › CMYK › 配置文件」中的配置文件输出打印油墨",
    "More": "更多",
    "More formats": "更多格式",
    "Other formats: TIFF and PDF, and EXR to keep light brighter than white":
        "其他格式：TIFF 和 PDF；EXR 可保留比白色更亮的光",
    "Other formats: TIFF and PDF": "其他格式：TIFF 和 PDF",
    "No profile": "无配置文件",
    "CMYK – %@": "CMYK – %@",
    "sRGB": "sRGB",
    "×": "×",
    "·": "·",
    "%@ × %@ in at %lld DPI": "%@ × %@ 英寸 · %lld DPI",

    # --- Filter panels (FilterSheet) ---
    "Click and drag two points on canvas": "在画布上点击并拖动两个点",
    "Linear blurs along the line; Radial keeps the start sharp and blurs outwards":
        "线性：沿线条方向模糊；径向：起点保持清晰，向外模糊",
    "The blur where the line starts": "线条起点处的模糊量",
    "The blur where the line ends, and past it": "线条终点及其后方的模糊量",
    "Swap From and To: blur the start and sharpen toward the end": "交换起点和终点：起点模糊，向终点方向锐化",
    "From": "起点",
    "To": "终点",

    # --- Shapes (ShapeControls, ShapeKind) ---
    "Line": "直线",
    "Fill color": "填充颜色",
    "Smooth Corners": "平滑圆角",
    "Set a radius above 0 to use smooth corners.": "将半径设为大于 0 才能使用平滑圆角。",
    "Use smooth squircle corners at 60% smoothing, matching Figma's iOS setting":
        "使用 60% 平滑度的圆角矩形（squircle），与 Figma 的 iOS 设置一致",

    # --- Keyboard shortcut editor (KeyboardShortcuts) ---
    "Toggle Fullscreen: the canvas alone on black (Esc also leaves)":
        "切换全屏：只留画布与黑色背景（Esc 也可退出）",
    "Click a shortcut, then press its new key combination, or ⊗ to remove it. Changes apply when you save.":
        "点击一个快捷键，然后按下新的组合键；点 ⊗ 可移除。保存后生效。",
    "Remove this shortcut": "移除此快捷键",
    "None": "无",
    "Delete": "Delete",
    "Return": "Return",
    "Esc": "Esc",
    "Tab": "Tab",
    "Space": "Space",

    # --- Selection editing (LassoControls) ---
    "%@ the selection by this many pixels": "将选区%@这么多像素",
    "Enter a whole number from 1 to %lld px.": "请输入 1 到 %lld 之间的整数（单位：像素）。",

    # --- Camera Raw main panel help (CameraRawControls) ---
    "RGB histogram": "RGB 直方图",
    "Shadow Clipping Indicator": "暗部溢出提示",
    "Highlight Clipping Indicator": "高光溢出提示",
    "Show clipped shadows in blue on the preview.": "在预览中用蓝色显示溢出的暗部。",
    "Show clipped highlights in red on the preview.": "在预览中用红色显示溢出的高光。",
    "Tones from black on the left to white on the right: blacks, shadows, midtones, highlights, whites. Control-click to show the vectorscope.":
        "从左到右为黑到白：黑色、阴影、中间调、高光、白色。按住 Control 点按可显示矢量示波器。",
    "Hue around the wheel, saturation outward from the center. Control-click to show the histogram.":
        "色相环绕色轮，饱和度由中心向外。按住 Control 点按可显示直方图。",
    "Brightens or darkens the whole picture, in stops of light. Hold Option to see clipped highlights.":
        "以曝光级数整体调亮或调暗画面。按住 Option 可查看溢出的高光。",
    "Makes light and dark tones more or less different, mostly around the middle.":
        "让明暗色调的差别更大或更小，主要作用于中间调。",
    "Adjusts the bright parts of the picture. Hold Option to see clipped highlights.":
        "调整画面明亮的部分。按住 Option 可查看溢出的高光。",
    "Adjusts the dark parts of the picture. Hold Option to see clipped shadows.":
        "调整画面暗黑的部分。按住 Option 可查看溢出的暗部。",
    "Sets the brightest point. Hold Option to see clipped highlights.":
        "设定最亮点。按住 Option 可查看溢出的高光。",
    "Sets the darkest point. Hold Option to see clipped shadows.":
        "设定最暗点。按住 Option 可查看溢出的暗部。",
    "Shifts the picture from blue to yellow.": "把画面由蓝色调向黄色。",
    "Shifts the picture from green to mauve.": "把画面由绿色调向紫红色。",
    "Strengthens quiet colors more than colors that are already strong, and protects skin tones.":
        "对不鲜艳的颜色比已经鲜艳的颜色增强更多，并保护肤色。",
    "Strengthens or weakens every color by the same amount.": "以相同幅度整体增强或减弱所有颜色。",
    "Adds or softens small detail.": "增强或柔化细节纹理。",
    "Adds or softens contrast along broader shapes.": "增强或柔化较大形状的对比度。",
    "Clears haze when raised, and adds haze when lowered.": "提高时去雾，降低时加雾。",
    "Spreads a glow from the bright areas.": "让明亮区域散发辉光。",
    "Chooses how bright an area must be to glow. Has no effect until Glow is raised.":
        "设定区域要多亮才会发光。提高「辉光」前不起作用。",
    "Sets how far the glow reaches. Has no effect until Glow is raised.":
        "设定辉光的扩散范围。提高「辉光」前不起作用。",
    "Shifts the glow from cool to warm. Halation stays red. Has no effect until Glow is raised.":
        "让辉光由冷向暖偏移；光晕始终偏红。提高「辉光」前不起作用。",
    "Darkens or lightens the edges. The center does not change.": "压暗或提亮边缘。中心不变。",
    "Sets where the vignette begins, from the center outward.": "设定暗角从中心向外的起始位置。",
    "Makes the vignette rounder or more square.": "让暗角更圆或更方。",
    "Softens the edge of the vignette.": "柔化暗角的边缘。",
    "Protects bright pixels while a dark vignette is applied. Used by Highlight Priority.":
        "施加暗角时保护明亮像素。「高光优先」会用到。",
    "Adds film grain, strongest in the middle tones.": "添加胶片颗粒，中间调最明显。",
    "Makes the grain coarser or finer.": "让颗粒更粗或更细。",
    "Makes the grain smoother or more uneven.": "让颗粒更平滑或更斑驳。",
    "Reset %@ to its defaults": "将%@重置为默认值",
    "Reset %@": "重置%@",

    # --- Camera Raw curves / mixer / grading (CameraRawColorControls) ---
    "Drag up or down to lift or lower those tones. Drag a divider along the bottom to change which tones each region covers.":
        "上下拖动可提升或压低这些色调。沿底部分隔条拖动可改变每个区域覆盖的色调。",
    "Drag a point. Click to add one. Double-click a point to remove it.":
        "拖动控制点；单击可添加控制点，双击控制点可将其移除。",
    "Lifts or lowers the brightest tones.": "提升或压低最亮的色调。",
    "Lifts or lowers the light tones.": "提升或压低较亮的色调。",
    "Lifts or lowers the dark tones.": "提升或压低较暗的色调。",
    "Lifts or lowers the darkest tones.": "提升或压低最暗的色调。",
    "In %lld   Out %lld": "输入 %lld   输出 %lld",
    "How much the curve also changes color strength. Zero matches Photoshop; lower keeps it to brightness, higher adds more color.":
        "曲线同时改变颜色强度的程度。0 与 Photoshop 一致；更低只改变亮度，更高会加入更多颜色。",
    "Drag on the picture to move the curve for the tone under the pointer.":
        "在画面上拖动，可移动指针所指色调的曲线。",
    "Shifts the selected color family around the wheel.": "让所选色系沿色轮偏移。",
    "Makes the selected color family stronger or quieter.": "让所选色系更浓或更淡。",
    "Makes the selected color family lighter or darker.": "让所选色系更亮或更暗。",
    "Shifts the picked color around the color wheel.": "让所拾取的颜色沿色轮偏移。",
    "Makes the picked color stronger or quieter.": "让所拾取的颜色更浓或更淡。",
    "Makes the picked color lighter or darker.": "让所拾取的颜色更亮或更暗。",
    "How far in hue the adjustment reaches.": "调整在色相方向的作用范围。",
    "How far in saturation the adjustment reaches.": "调整在饱和度方向的作用范围。",
    "How far in brightness the adjustment reaches.": "调整在明度方向的作用范围。",
    "Controls how much the three tonal wheels overlap.": "控制三个色调色轮之间的重叠程度。",
    "Shifts the wheels toward shadows or highlights.": "让色轮偏向暗部或高光。",
    "Brightness added by this wheel.": "此色轮加入的亮度。",

    # --- Camera Raw detail and optics (CameraRawDetailOpticsControls) ---
    "Controls how strong the sharpening is.": "控制锐化的强度。",
    "How far from each edge the sharpening reaches, in pixels.": "锐化从每条边缘延伸的距离（像素）。",
    "Emphasizes fine texture over broader edges.": "强调细微纹理，而非较大的边缘。",
    "Limits sharpening to stronger edges. Hold Option to see the mask.":
        "只锐化较强的边缘。按住 Option 可查看蒙版。",
    "Smooths grain and noise in brightness.": "平滑亮度的颗粒与噪点。",
    "Preserves fine texture while luminance noise is reduced.": "在减少亮度噪点的同时保留细微纹理。",
    "Keeps local contrast after luminance smoothing.": "亮度平滑后保留局部对比度。",
    "Smooths colored speckles.": "平滑彩色斑点。",
    "Preserves colored edges while color noise is reduced.": "在减少颜色噪点的同时保留彩色边缘。",
    "Makes the color smoothing softer or tighter.": "让颜色平滑更柔和或更紧凑。",
    "How much of the profile distortion correction is applied.": "配置文件畸变校正的应用程度。",
    "How much of the profile vignetting correction is applied.": "配置文件暗角校正的应用程度。",
    "Straightens barrel or pincushion bending.": "校正桶形或枕形弯曲。",
    "Weakens purple fringes inside the purple hue range.": "减弱紫色色相范围内的紫边。",
    "Hue range where purple defringe runs.": "紫色去边生效的色相范围。",
    "Weakens green fringes inside the green hue range.": "减弱绿色色相范围内的绿边。",
    "Hue range where green defringe runs.": "绿色去边生效的色相范围。",
    "Brightens or darkens the corners to counter lens falloff.": "提亮或压暗四角，抵消镜头暗角。",
    "Moves the vignette correction inward or outward.": "让暗角校正向内或向外移动。",
    "Purple": "紫色",

    # --- Camera Raw geometry and calibration (CameraRawGeometryCalibrationControls) ---
    "Version": "版本",
    "Straightens vertical lines toward the center.": "把垂直线校正向中心。",
    "Straightens horizontal lines toward the center.": "把水平线校正向中心。",
    "Rotates the picture around its center.": "围绕中心旋转画面。",
    "Stretches width relative to height.": "相对高度拉伸宽度。",
    "Zooms the transformed picture within the frame.": "在画框内缩放变换后的画面。",
    "Moves the picture left or right.": "左右移动画面。",
    "Moves the picture up or down.": "上下移动画面。",
    "Adds green or magenta to the darkest tones.": "为最暗的色调加入绿色或洋红色。",
    "Shifts how red is interpreted.": "调整红色的解释方式。",
    "Strengthens or weakens the red primary.": "增强或减弱红色原色。",
    "Shifts how green is interpreted.": "调整绿色的解释方式。",
    "Strengthens or weakens the green primary.": "增强或减弱绿色原色。",
    "Shifts how blue is interpreted.": "调整蓝色的解释方式。",
    "Strengthens or weakens the blue primary.": "增强或减弱蓝色原色。",

    # --- Color Range (ColorRangeSheet) ---
    "Shift-click adds a color, Option-click takes one away.":
        "按住 Shift 点按可添加颜色，按住 Option 点按可减去颜色。",
    "Click the image to pick the color to select.": "点按图像以拾取要选择的颜色。",
    "Click the image to select that color": "点按图像以选择该颜色",
    "Click the image to add that color to the selection": "点按图像以将该颜色加入选区",
    "Click the image to take that color out of the selection": "点按图像以将该颜色从选区中移出",

    # --- Layers and canvas (NativeLayerList, FloatingSelection, SelectionClipboard, Gradient) ---
    "HDR layer: keeps light brighter than white, shown as white": "HDR 图层：保留比白色更亮的亮度，显示为白色",
    "16-bit layer: keeps 16 bits a channel": "16 位图层：每通道保留 16 位",
    "HDR": "HDR",
    "16-Bit": "16 位",
    "Editable text": "可编辑文本",
    "Expand or collapse folder": "展开或折叠文件夹",
    "Create clipping mask": "创建剪贴蒙版",
    "Release clipping mask": "释放剪贴蒙版",
    "Convert to 16-Bit": "转换为 16 位",
    "Convert to 8-Bit": "转换为 8 位",
    "Floating Selection": "浮动选区",
    "Pasted Image": "粘贴的图像",
    "Gradient Mask": "渐变蒙版",
    "Layer Effects": "图层效果",
    "Canvas Extension": "扩展画布",
    "Progressive Blur": "渐进模糊",

    # --- PSD import notes and error text (PSD, ImageTrim, EditorSession, brush) ---
    "Only 8-bit RGB and CMYK Photoshop files can be imported.":
        "只能导入 8 位 RGB 和 CMYK 的 Photoshop 文件。",
    "Cropped to the canvas so the file fits in memory. Pixels outside the canvas weren't imported.":
        "已裁剪到画布范围，以便文件装入内存。画布之外的像素未被导入。",
    "The Photoshop stroke isn’t supported on shape layers and was omitted.":
        "形状图层不支持 Photoshop 描边，已忽略。",
    "No content remained after trimming.": "修剪后没有剩余内容。",
    "The trimmed image dimensions are invalid.": "修剪后的图像尺寸无效。",
    "Couldn’t trim image": "无法修剪图像",
    "That profile isn’t a CMYK output profile.": "该配置文件不是 CMYK 输出配置文件。",
    "“%@” has no images to import.": "“%@”里没有可导入的图像。",
    "Option-click where Clone Stamp should copy from first.": "请先按住 Option 点按，设置仿制图章的取样源。",

    # --- History-action names (Selection, TypeTool, SelectionEdits, DeepLayers) ---
    "Polygonal Lasso": "多边形套索",
    "Elliptical Marquee": "椭圆选框",
    "Rectangular Marquee": "矩形选框",
    "Feather Selection": "羽化选区",
    "Duplicate Pixels": "复制像素",
    "Move Pixels": "移动像素",
    "New Text Layer": "新建文本图层",
    "Fill Text": "填充文本",

    # --- Grid settings (GridSettingsSheet) ---
    "A subdivision every %@ pixels.": "每 %@ 像素一条子网格线。",
    "Use gridlines every %lld–%@ pixels and %lld–%lld subdivisions, no more than the pixels between gridlines.":
        "网格线间隔 %lld–%@ 像素、子网格 %lld–%lld 条，且不能超过网格线之间的像素数。",

    # --- Misc panels (Navigator, zoom cursors, presets, canvas) ---
    "Click or drag to move the view": "点按或拖动可移动视图",
    "Untitled %lld": "未命名 %lld",
    "Zoom in": "放大",
    "Zoom out": "缩小",
    "%lld DPI": "%lld DPI",
    "%@ uncompressed RGBA canvas": "%@ 未压缩 RGBA 画布",
    "Camera Raw…": "Camera Raw…",
    "Import, then open the Camera Raw Filter": "先导入，再打开 Camera Raw 滤镜",
    "Instagram Square": "Instagram 方形",
    "Instagram Portrait": "Instagram 竖版",
    "Instagram Story": "Instagram 快拍",
    "YouTube Thumb": "YouTube 缩略图",
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
