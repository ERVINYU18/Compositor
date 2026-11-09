# v1.6.6 conflict resolution

Round: 1.6.4 → 1.6.6, merged by hand on 2026-11-09. The round carries
**v1.6.5** as well; it was never merged separately. The updater hit the same
content conflicts and rolled back cleanly at 08:49.

## 1 Where the official source came from

- Upstream tag `v1.6.6` = `2f507800bc4b32db6b31d34a822cbfc577bf46cf`
  (`git ls-remote --tags upstream` through Clash on 127.0.0.1:7897).
- Source: `https://codeload.github.com/robbietilton/Compositor/tar.gz/refs/tags/v1.6.6`,
  sha256 `24b64838527cbc9e5956d6f3719fde69a240eec77e2fdbc6941dcb88883bed47`, 4.2 MB.
- Synthetic snapshot commit **`934d1e0`**, parent = the v1.6.4 snapshot
  `4eed49a`. **Not** the real upstream tag commit — the ancestry chain is built
  from tarballs.
- Merge commit **`ed7a6dc`**, parents `26f14c8` (the Chinese release commit)
  and `934d1e0`. The snapshot branch is an ancestor of HEAD.
- Version/build after the merge: **1.6.6 / 65**. Bundle ID remains
  `com.wonderassembly.compositor.cn`.

### Version gaps

Checked before starting: 1.6.4 → 1.6.5 → 1.6.6, with 1.6.5 never merged. All
its changes are present in this round.

## 2 What upstream changed

37 files, `+934 / -439`.

| Area | Change |
|---|---|
| Sliders | `SliderSnap` (the global NSSlider cell adjustment) is removed and replaced by `AppSlider`, a SwiftUI track view; `CameraRawSlider` becomes a SwiftUI `View` built on `SliderTrackView`; the RAW develop sheet and the other panels adopt `AppSlider` |
| Export / Save | Export As remembers the format per document and the last format between launches; Export and Save start from the source image's name, folder and format; a new `exportName` / `startingFormat` helper |
| Brush | Stroke recovery and stroke effects; new `BrushRecoveryTests` and `StrokeEffectTests` |
| Colour picker | Shows the current colour and the colour before it, with a help string on the "before" swatch |
| Tests | `SliderSnapTests` removed with `SliderSnap`; `CameraRawSliderTests` rewritten; new `ImageSourceTests` |

New files: `AppSlider.swift`, `BrushRecoveryTests.swift`, `ImageSourceTests.swift`,
`StrokeEffectTests.swift`. Removed: `SliderSnap.swift`, `SliderSnapTests.swift`.
Xcode's synchronized folder groups mean no project-file entries were needed
beyond the version/build numbers.

## 3 Every conflict, and which side won

Five paths conflicted, exactly as the pre-merge simulation predicted. The
updater hit the same five and rolled back; its transaction backup branch is
`backup-cn-v2-20261109-084948`.

### `Compositor.xcodeproj/project.pbxproj`

Upstream changed only the version and build number. **Took 1.6.6 / 65**, kept
the `.cn` bundle ID and the app target's four signing settings
(`CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`,
`DEVELOPMENT_TEAM = ""`, `ENABLE_HARDENED_RUNTIME = NO` in Debug and Release).

### `Compositor/IO/ProjectController.swift` (two conflicts)

Upstream added `exportName` / `startingFormat`, the per-document and persisted
last-export format, and source-image defaults for the save panels. **Took the
upstream behaviour** and kept the localized panel titles
(`String(format: localizedString("Export %@"), …)`,
`localizedString(asNew ? "Save Project As" : "Save Project")`). The
`exportName` fallback `"Untitled"` is localized so the suggested file name stays
Chinese; `ImageSourceTests` now asserts it through `localizedString("Untitled")`.
The save-project panel keeps `localizedString("Untitled.comp")`.

### `Compositor/UI/CameraRawSlider.swift`

Upstream completely rewrote the slider from an `NSViewRepresentable`
(`CameraRawSliderView`, `GradientSliderCell`, manual tracking) into a SwiftUI
`View` over `SliderTrackView`. **Took the upstream rewrite** — the old AppKit
implementation is gone — and re-applied `localizedString(help)` to the `.help`
and `.accessibilityLabel` modifiers. No `CameraRawSliderView` /
`GradientSliderCell` references remain.

### `Compositor/UI/RawDevelopSheet.swift`

Upstream swapped `Slider` for `AppSlider`. **Took `AppSlider` and kept
`Text(verbatim: localizedString(title))`** for the row label.

### `CompositorTests/SliderSnapTests.swift` (modify/delete)

Upstream deleted the file together with `SliderSnap`; the Chinese branch had
test-stability edits (async geometry wait). **Removed the file**, since the API
it tested no longer exists. No `SliderSnap` references remain anywhere.

## 4 Automatically merged files: spot checks

The other 18 files that both sides touched merged cleanly: `CompositorApp`,
`EditorSession+Brush`, `EditorSession`, `LayerEffects`, `ProjectWorkspace`,
`CompositorApplicationDelegate`, `BrushControls`, `ColorPickerSheet`,
`ColorRangeSheet`, `EffectsSheet`, `ExportAsSheet`, `FilterSheet`,
`GradientControls`, `GridSettingsSheet`, `HueSaturationSheet`,
`KeyboardShortcuts`, `LassoControls`, `ShapeControls`. Their `localizedString`
counts are unchanged (for example `ExportAsSheet` 20, `KeyboardShortcuts` 10,
`ColorRangeSheet` 6, `FilterSheet` 9); no localization call was lost.
`CompositorApplicationDelegate` no longer calls `SliderSnap.install()`.

`audit_strings.py` reports **0 UI literals not in the catalog**. It still counts
the empty-string key `""` as lacking zh-Hans; that key is present in earlier
baselines too and is not a regression.

## 5 Localization and verification results

- Catalog: **1562 → 1564 keys (+2)**:
  - `Current color`
  - `The color before: click to go back to it`
- `AppSlider` / `CameraRawSlider` expose only a numeric accessibility value
  (`"%.0f"`), which is not a translatable key.
- `xcrun swiftc -parse` on the 34 changed Swift files: all parsed (syntax only;
  the real check is the build).
- Release build: `BUILD SUCCEEDED`. Product: **1.6.6 (65)**,
  `com.wonderassembly.compositor.cn`, ad-hoc signature, no Team ID.
- Full Debug test run:
  `xcrun xcresulttool get test-results summary` → **806 total, 806 passed,
  0 failed, 0 skipped**.
- Release smoke: the DerivedData product stayed alive for 7 seconds, its main
  thread sampled in `ReceiveNextEventCommon`, then quit cleanly.
- The compiled `zh-Hans.lproj` contains the new strings (当前颜色,
  之前的颜色：点按可返回).
- Installed on 2026-11-09 after backing up 1.6.4 to
  `.Compositor-CN-Backups/pre-1.6.6-install-20261109-091952/`. The installed app
  reports **1.6.6 (65)**, ad-hoc, no Team ID, and passed the installed smoke.
  The user reported manual acceptance passed.

## 6 Release

- Release tag: `v1.6.6-cn`, on the commit that carries this record.
- `compositor-cn.snapshot-tag` is set to `v1.6.6`; the snapshot branch
  `compositor-upstream-snapshot` is `934d1e0` and is an ancestor of HEAD.
- Archive: `.Compositor-CN-Backups/post-1.6.6-cn-<timestamp>/` and its iCloud
  mirror, each verified with `shasum -c`.
- The branch and tag are pushed after this record; see the archive's
  `STATE--*.txt` for the final commit and test numbers.

## 7 Manual acceptance focus

The user's acceptance pass covered this round. Keep these areas in mind for the
next regression:

1. AppSlider across Brush / Shape / Type / Transform / Filter / Effects / RAW:
   track click jumps, double-click resets, Chinese help and accessibility.
2. Export As format memory; Export/Save default name, folder and format from the
   source image; Chinese "Untitled" fallback.
3. Colour picker current/previous swatches and the Chinese "before" help.
4. Brush stroke recovery and stroke effects.
5. Old `.comp` projects, PSD/PSB, Camera RAW, import/export.
