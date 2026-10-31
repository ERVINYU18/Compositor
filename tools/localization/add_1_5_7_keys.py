#!/usr/bin/env python3
"""Add the zh-Hans entries official v1.5.7 needs to Localizable.xcstrings.

Same conventions as add_1_4_9 / add_1_4_10 / add_1_5_3 / add_1_5_5 / add_1_5_6:
  * back the catalog up before touching it;
  * refuse to write unless re-serialising the untouched catalog reproduces the
    original bytes exactly (the file has NO trailing newline);
  * append new keys at the end of "strings", never overwriting existing
    translations;
  * fill in zh-Hans for keys that exist but have no Chinese yet;
  * refuse to run while merge conflict markers remain.

Sources for the 1.5.7 cycle:
  * the official diff by hand: Lens Effects (one filter, five effects, each with
    its own controls), and the GIF timeline's "Original" delay label, which
    upstream rewrote as "<delays> · Original";
  * the updater's own DynamicEnglish.txt, which flagged the two
    `Text($0.rawValue)` pickers (now `Text(verbatim: $0.localizedName)`);
  * a sweep of every literal in the touched files, which also catches what the
    audit's sink regex misses: `control("Length", …)` and friends reach the UI
    through `localizedString(title)` inside the helper.

Deliberately NOT translated:
  * LensEffect / BokehShape raw values are their own display keys ("Anamorphic
    Flare", "Cat's Eye", …) — the raw value stays English for any future
    Codable use, only the catalog supplies Chinese.
  * "ms" and "fps" stay in the numeric labels, as Photoshop's do.
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
    # --- FilterKind: the new Lens Effects entry in the filter menu ---
    "Lens Effects": "镜头效果",

    # --- Lens Effects: the effect picker and its per-effect slider labels ---
    "Effect": "效果",
    "Points": "点数",
    "Length": "长度",
    "Copies": "份数",
    "Reach": "延伸",
    "Brightness": "亮度",
    "Ring": "环边",

    # --- LensEffect's raw values, shown in the effect picker ---
    "Anamorphic Flare": "变形镜头光晕",
    "Starburst": "星芒",
    "Mist": "雾化",
    "Prism": "棱镜",
    "Bokeh": "散景",

    # --- BokehShape's raw values, shown in the shape picker ---
    "Round": "圆形",
    "Hexagon": "六边形",
    "Oval": "椭圆",
    "Cat's Eye": "猫眼",

    # --- Lens Effects: each control's help ---
    "How far the streaks reach across the picture":
        "光条在画面中延伸多远",
    "How bright a light has to be to flare":
        "光线要多亮才会产生光晕",
    "How far the lens's coatings turn each streak blue along its length; "
    "none keeps the light's own color":
        "镜头镀膜让每条光晕沿其长度变蓝的程度；为零时保留光线原本的颜色",
    "How far the spikes reach":
        "星芒尖角延伸多远",
    "How bright a light has to be to sparkle":
        "光线要多亮才会产生星芒",
    "How many spikes each light has, as the lens's aperture blades make them":
        "每个光源的尖角数量，由镜头光圈叶片决定",
    "How much light scatters: a soft halo around bright areas, and gently lifted shadows":
        "光线散射的程度：亮部周围形成柔和光晕，暗部被轻轻提亮",
    "How far the light spreads":
        "光线扩散多远",
    "How many times the picture echoes, each fainter":
        "画面重影的次数，每层更淡",
    "How far apart the copies are":
        "各重影之间的距离",
    "Which way it's pushed, toward the edge the prism sits at":
        "重影朝哪个方向偏移，即棱镜所在的那一边",
    "How far into the frame the copies show from that edge":
        "重影从该边缘向画面内延伸多远",
    "How far out of focus: the size of each disc":
        "失焦程度：每个光斑的大小",
    "How brightly lights open into discs":
        "光源散开成光斑的亮度",
    "Light gathered at each disc's rim, as some lenses draw it":
        "光斑边缘聚集的光，某些镜头的成像特征",
    "The aperture's shape: round wide open, a hexagon of blades, "
    "an anamorphic oval, or a cat's eye toward the edges":
        "光圈形状：全开时为圆形，收小后呈叶片构成的六边形，变形镜头为椭圆，画面边缘为猫眼形",

    # --- The animation timeline: upstream now spells out the original delays ---
    "%@ · Original": "%@ · 原始",
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
