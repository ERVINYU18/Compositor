# v1.5.11 conflict resolution

Round: 1.5.9 → 1.5.11, done by hand on 2026-10-27 after the updater (V2.2.1)
rolled the merge back on three content conflicts.

## Where the official source came from

- Upstream tag `v1.5.11` = `9959c32d77330ec8d7b42a49353d903283ecb8e6` (`git ls-remote`
  through Clash on 127.0.0.1:7897 — the sandbox proxy still 502s on `git`).
- Source: `https://codeload.github.com/robbietilton/Compositor/tar.gz/refs/tags/v1.5.11`,
  sha256 `36fdf9fcbbd0fd8ab01a6901177865562a32431753008d5bf0ac40e0fa88d58c`, 4.1 MB.
- Synthetic snapshot commit **`02daaea`**, parent = the v1.5.9 snapshot `88ef9c1`.
  **Not** the real upstream tag commit — the ancestry chain is built from tarballs,
  as it has been since 1.5.7.

### This round skips a version

The updater went straight from 1.5.9 to 1.5.11: v1.5.10 was never merged on its
own, so **this round carries both releases** (34 files, +797/−97 against 1.5.9).
The 1.5.10→1.5.11 delta was checked separately and is a subset: EditorSession,
LensEffects, ProjectStore, EditorCanvas, ColorPaletteControls, ColorPickerSheet,
FilterSheet, ToolRail, pbxproj, four test files, appcast, two docs.

### Why the updater rolled back

Three content conflicts — `project.pbxproj`, `EditorSession.swift`,
`CropControls.swift` — which is a genuine conflict, not the
`APP_PATCH_FAILED` ordering bug from 1.5.9 (that one trips on
`CompositorApp.swift`, and this round merged that file cleanly). The rollback
was clean; `last-conflicts.txt` matches what the manual merge hit.

## What upstream v1.5.11 brings

| Area | Change |
|---|---|
| Layer alignment (new) | `LayerAlign.swift`: `LayerAlignment` (six) + `LayerDistribution` (four), reachable from the Layer menu and an Align popover in the Move bar; a selected folder moves as one; one undo step; offsets rounded to whole pixels |
| Sharpen (new) | Filter **and** adjustment kind; a Core Image unsharp mask, so it runs 16-bit on the GPU like Bloom/Glow |
| Project format | `ProjectManifest.current` 18 → **20** (19 = Sharpen layer, 20 = Lens Effects fringe) |
| Crop | Ratio list grouped by shape, custom W:H popover, `CropGeometry.ratio` accepts any `W:H`; **"Original" renamed "Canvas"** |
| Lens Effects | New `prismFringe` (default 30) replaces the fixed 0.3% red/blue split |
| Move bar | Flip buttons become icon-only; number fields size to their digits (`ToolHeaderStyle.threeDigits` / `fiveDigits`) |
| Session | `canEditLayers` now excludes a pending transform; `canEditLayersOnceTransformCommitted` for commands that commit it first |

## The three conflicts

### `Compositor.xcodeproj/project.pbxproj` (two identical blocks, Debug and Release)

Both sides only differ in the version line and the bundle ID.

Resolution: upstream's `MARKETING_VERSION = 1.5.11` and `CURRENT_PROJECT_VERSION = 57`,
our `PRODUCT_BUNDLE_IDENTIFIER = com.wonderassembly.compositor.cn`.

Signing sentinels re-verified on the App target after the merge (lines 414–421 and
454–461):

```
CODE_SIGN_IDENTITY = "-"; CODE_SIGN_STYLE = Manual;
DEVELOPMENT_TEAM = ""; ENABLE_HARDENED_RUNTIME = NO;
```

The two `DEVELOPMENT_TEAM = 3E4X3B9Z9T` entries (lines 319, 386) and the four in the
tests/uitests targets are the baseline from 1.4.7 — not a regression.

### `Compositor/Document/EditorSession.swift` (`NavigationTool`)

Upstream changed one SF Symbol: the hand tool went from `hand.draw` to `hand.raised`,
because `ToolRail` now mirrors it (`scaleEffect(x: -1)`) so the thumb lands on the
left. Upstream also dropped the `localizedString(...)` wrapper around `label`.

Resolution: took upstream's `hand.raised` **and** kept our wrapper. `.help(...)` and
`.accessibilityLabel(...)` receive a `String` here, and the `StringProtocol` overloads
are verbatim — without the wrapper the tool tips go back to English.

### `Compositor/UI/CropControls.swift` (the ratio Picker)

Upstream replaced the flat ratio array with grouped `ratioGroups` + a `ratioSelection`
binding + a custom-ratio popover, and spelled the menu items `Text($0)`.

Resolution: kept upstream's structure and popover, but every ratio goes through
`localizedString`:

```swift
ForEach(ratioGroups[index], id: \.self) { Text(verbatim: localizedString($0)) }
...
Text(verbatim: localizedString(session.cropRatioChoice)).tag(session.cropRatioChoice)
```

The **stored** choice stays English, so `ratioSelection`, `CropGeometry.ratio` and the
`.tag(...)` values still see `"Canvas"` / `"4:3"` / `"Custom"`. Only the label is
translated.

## Auto-merged files that needed checking

Upstream rewrote whole blocks of these without conflicting, so they were diffed by
hand (the 1.5.7 FilterSheet lesson):

- `CompositorApp.swift` — new `Menu("Align")` / `Menu("Distribute")` with
  `Button(alignment.rawValue)`. Fixed to `Button(alignment.localizedName)`.
- `TransformInspector.swift` — new `AlignButton` popover; its icon titles were built as
  `"Align " + alignment.rawValue`. Fixed to the same `localizedName`, and the
  distribute hint now goes through `String(format: localizedString("%@ (three or more layers)"), ...)`.
  The pre-existing `Text(verbatim: $0.localizedName)` for `LayerSampling` survived.
- `FilterSheet.swift` — new `case .sharpen` controls and the Fringe control; all
  literals, so they only needed catalog keys.
- `LayersPanel.swift` / `CompositorApp.swift` filter menus — reach the catalog through
  `kind.localizedName`, so `Sharpen` just needed a key.
- `ProjectStore.swift` — `current = 20`; our `errorDescription` reads
  `Int64(ProjectManifest.current)` so it now says "1–20" without a code change.

No upstream symbol was deleted this round (checked: the only `-` lines carrying
declarations are modified ones), so the 1.5.8 `upstreamVersions` class of breakage
does not apply.

## Localization: 1471 → 1502 (+31, no removals)

New keys, all added by `02-localization/add_1_5_11_keys.py`:

- **Align / Distribute** (12 + 2): `Align`, `Distribute`, and one key per case —
  `Align Left Edges`, `Align Horizontal Centers`, `Align Right Edges`,
  `Align Top Edges`, `Align Vertical Centers`, `Align Bottom Edges`,
  `Distribute Horizontal Centers`, `Distribute Vertical Centers`,
  `Distribute Horizontal Spacing`, `Distribute Vertical Spacing`,
  plus `%@ (three or more layers)` and the Align popover's help text.
- **Crop** (5): `Custom…`, `Custom ratio`, `Width:Height`,
  `Width:height, such as 4:5 or 3:2`, `Enter a positive ratio within the document size limits.`
- **Sharpen** (3): `Sharpen`, and the two control hints.
- **Lens Effects** (2): `Fringe`, and its hint.
- **Line tool** (6): `Solid`, `Dotted`, `Dashed`, `Long Dash`, `Round Cap`, `Square Cap`.
- **Channel Pack** (1): `Alpha`.

### Why Align and Distribute cannot use `localizedName`

`LayerAlignment.horizontalCenter` and `LayerDistribution.horizontalCenters` are both
spelled `"Horizontal Centers"`. Chinese needs 水平居中**对齐** for one and
水平居中**分布** for the other, so a shared raw-value key would collapse them. Each
enum therefore gets a `localizedName` that switches over its own prefixed keys, and
`LayerAlign.swift` uses the same strings for the undo-step names, so Undo reads
「左边缘对齐」 rather than "Align Left Edges".

### Four pre-existing leaks fixed this round

These are invisible to `audit_strings.py` — enum raw values reaching the screen
through a `String`/`StringProtocol` overload rather than a literal:

1. `ShapeLineStyle` and `ShapeLineCap` in the Line tool's Style and Cap menus, and as
   accessibility labels. The 1.5.9 note claimed these were "not shown as menu titles";
   that was wrong — `Label { Text(cap.rawValue) }` renders in the menu.
   Caps get their own keys because the catalog's existing `Square` / `Round` are
   shapes (正方形 / 圆形), which read wrong for a line's ends → `Square Cap` / `Round Cap`.
2. `ChannelPack.Channel` — `Text(channel.rawValue)` and `Picker(channel.rawValue, ...)`
   in the export sheet. Now `channel.localizedName`.
3. `ColorPickerSheet` — the R/G/B accessibility label was a ternary producing a
   `String`, so it bypassed localization.
4. `PSDConversionSheet` — its title is built as `"Open “\(name)”?"` and shown with
   `Text(verbatim:)`, and its confirm button used a bare `"Import"`. Both now go
   through `localizedString`, reusing the existing `Open “%@”?` key.

`Text(unit.rawValue)` in `NewCanvasSheet` (px / mm / cm / in) was left alone: those are
units, not words.

## Old-project compatibility

- Format 18 → 20 is a bump, not a break: `FilterLayerSettings` decodes `sharpen` and
  `LensEffectSettings` decodes `prismFringe` with defaults, so a version-17 or -18 file
  opens with Sharpen absent and Fringe at 30.
- `ProjectManifest.supported` is `Set(1...current).union([27])`, so it widens by itself.
- `cropRatioChoice` is a plain `EditorSession` property reset to `"Free"` — **not**
  persisted — so renaming "Original" to "Canvas" needs no migration. A saved project
  never carries it.

## Verification

| Check | Result |
|---|---|
| Release build | `** BUILD SUCCEEDED **` |
| Debug test | `** TEST SUCCEEDED **`, **745 / 745 passed**, 0 failed, 0 skipped |
| Test delta | 1.5.9 = 734 → 1.5.11 = 745 (+11: `LayerAlignTests`, `CropTests`, `FilterLayerTests`, `GPUCanvasTests`, `LensEffectsTests`, `ProjectTests`) |
| Product | 1.5.11 / build 57 / `com.wonderassembly.compositor.cn` / adhoc / no team |
| Launch smoke | alive 7 s, `sample` shows the main thread in `ReceiveNextEventCommon` (idle, not hung) |
| Compiled catalog | `zh-Hans.lproj/Localizable.strings` spot-checked: 锐化 / 色散 / 左边缘对齐 / 水平居中分布 / 圆头 / 透明度 / 自定义比例 / 实线 all present |
| Screenshot | main window renders fully Chinese; the Move bar's new 对齐 button is there |

The build and test now run **from this session** — `xcodebuild` cannot run inside
WorkBuddy's own seatbelt (`sandbox-exec: sandbox_apply: Operation not permitted`,
even with the outer sandbox off), so the script is handed to a real Terminal via
`open -n -a Terminal` plus GUI automation. See `AGENTS.md`.

## Manual acceptance focus

1. Layer menu → 对齐 / 分布 on a multi-layer selection, and on a selected folder.
2. Move bar → 对齐 popover: all ten icons, their tooltips, and 撤销 wording.
3. 滤镜 → 锐化…, and 图层 → 新建调整图层 → 锐化…; check Amount / Radius hints.
4. Crop: the grouped ratio list, 画布 in place of 原始比例, and a custom ratio (try 5:4).
5. 镜头效果 → 色散 at 0 and at 100.
6. Line tool: 样式 and 端点 menus now Chinese.
7. Export → Channel Pack: rows read 红 / 绿 / 蓝 / 透明度.
8. Open a project saved by 1.5.9 to confirm format 18 still loads.
