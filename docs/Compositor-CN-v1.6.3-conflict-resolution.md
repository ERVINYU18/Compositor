# v1.6.3 conflict resolution

Round: 1.5.12 → 1.6.3, merged by hand on 2026-11-04. The round carries
**v1.6.0, v1.6.1 and v1.6.2** as well; none of those tags was ever merged
separately.

## 1 Where the official source came from

- Upstream tag `v1.6.3` = `5c3489e84c2d22da18566f40079f14f86296e57c`
  (`git ls-remote --tags upstream` through Clash on 127.0.0.1:7897).
- Source: `https://codeload.github.com/robbietilton/Compositor/tar.gz/refs/tags/v1.6.3`,
  sha256 `7600581368ebd90657ec84c3650788d6b394a324aff8bfa9ef6ff516f5668a94`, 4.2 MB.
- Synthetic snapshot commit **`7b0a388`**, parent = the v1.5.12 snapshot
  `9f77fe2`. **Not** the real upstream tag commit — the ancestry chain is built
  from tarballs, as it has been since 1.5.7.
- Merge commit **`70939b4`**, parents `1e64ffd` (the Chinese branch) and
  `7b0a388`. The snapshot branch is an ancestor of HEAD.
- Version/build after the merge: **1.6.3 / 62**. Bundle ID remains
  `com.wonderassembly.compositor.cn`.

### Version gaps

Checked before starting: 1.5.12 → 1.6.0 → 1.6.1 → 1.6.2 → 1.6.3, with
1.6.0–1.6.2 never merged. All their changes are present in this round.

## 2 What upstream changed

56 commits, 64 files, `+3873 / -306` (the merge commit shows `+4539 / -306`
because it also carries the Chinese localization and the conflict fixes).

| Area | Change |
|---|---|
| Volumetric Light | Fog lit by a light placed on the image; Haze, Distance, Depth Contrast, Intensity, Size, Shafts, Keep Subject Clear and the light's colour; picks a light from the photo's own highlights; Extract Depth adds the depth map as a layer |
| DepthMini | A ~2.6 MB depth model distilled from Depth Anything V2 Small, downloaded from the `depth-model-1` release on first use, checked by SHA-256, compiled and cached in Application Support; falls back to guessed depth when it cannot be had |
| Reduce Noise | Camera Raw's noise reduction as its own filter (Strength / Preserve Details / Color Noise), a GPU non-local-means path with a C fallback, and an adjustment layer whose settings enter **project format 21** |
| Layers | Right-click export of each selected layer as a trimmed PNG named after it; visibility, clipping and 16/8-bit conversion act on every selected layer; the panel footer becomes adjustment / filter / effect menus |
| Selection | Space-drag to move a marquee; number keys set opacity with the Marquee, Lasso and Magic Wand; the status bar shows the selection's size; sliver edges from Core Graphics are dropped |
| View / UI | Show Extras on ⌘H outside the Move tool; View › Show › Distances; shared edit-panel position; the window fills the screen after an update; Services removed from the app menu |
| Depth | 16-bit/HDR layers keep their depth through 8-bit edits; Image Size scrubbing uses the document limits; undo history stops at the document's start |

The new source files are `VolumetricLight.swift`, `LayerDistances.swift`,
`DepthModel.swift`, `GPUReduceNoise.swift`, `MetalNonlocalMeans.swift` and
`MetalVolumetricLight.swift`; the new test files are `VolumetricLightTests`,
`ReduceNoiseTests`, `LayerDistancesTests`, `LayerExportTests` and
`LayersFooterTests`. The project uses Xcode's synchronized folder groups, so no
new `PBXBuildFile` entries were needed.

## 3 Every conflict, and which side won

Six paths conflicted, exactly as the pre-merge simulation predicted.

### `.gitignore`

Upstream added `/DEPTH_MODEL_PLAN.md` and `/depth-model-results/`; the Chinese
branch had added `tools/localization/backups/` and `tools/localization/*.json`.
**Both kept.**

### `Compositor.xcodeproj/project.pbxproj`

Upstream's only changes were the version and build number (12 lines each way).
**Took 1.6.3 / 62**, kept the Chinese `PRODUCT_BUNDLE_IDENTIFIER`, and rechecked
the app target's four signing settings: `CODE_SIGN_IDENTITY = "-"`,
`CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`,
`ENABLE_HARDENED_RUNTIME = NO` in both Debug and Release.

### `Compositor/Document/ColorPalette.swift`

Upstream added the `.volumetricLight` picker target and the
`Color Picker (Light Color)` title; the Chinese branch had localized every
`colorPickerTitle` return. **Took the new case and routed it through
`localizedString("Color Picker (Light Color)")`**, whose entry already existed.

### `Compositor/UI/LayersPanel.swift`

Upstream moved the footer into a new `LayersFooter` component whose three menus
use `kind.rawValue`; the Chinese branch had replaced those with
`kind.localizedName`. **Took the new component and applied `localizedName` to
all three menus** (adjustments, filters, effects). `New filter layer` is a new
key; `New adjustment layer` and `Add layer effect` already existed.

### `Compositor/UI/LevelsSheet.swift`

Upstream moved Reset onto the histogram row and hid the Preview checkbox for
adjustment layers; the Chinese branch had localized the channel picker. **Took
the upstream layout and kept `Text(verbatim: $0.localizedName)` for the channel
picker**; the other localized channel/mode/field/accessibility strings were
preserved.

### `Compositor/UI/NativeLayerList.swift` (three conflicts)

Upstream changed the clipping, visibility and 16/8-bit items from single-layer
actions to multi-selection actions. **Took the upstream multi-selection
behaviour** and wrapped the new titles in `localizedString`:

- clipping: `localizedString(session.selectedClippingTitle)`;
- visibility: `localizedString(session.visibilityTitle)`;
- conversion: `localizedString("Convert to 16-Bit")` / `"Convert to 8-Bit"`.

The old single-layer `convertDepthAction` and `convertHDRToSixteenAction`
selectors are gone; no test or source still references them.

## 4 Automatically merged files: spot checks

The remaining 19 files that both sides touched merged cleanly. The existing
`localizedString(` calls survived in every one (for example `FilterSheet` 9,
`ProjectController` 17 before the new export UI, `CompositorApp` 10 before the
new menu items), but upstream's new code is English by default, so these were
checked by hand and fixed:

- `ContentView`: the new shape/selection size labels interpolated English
  `Line` / `Shape` / `Selection`; now built with `localizedString` and
  `String(format:)`.
- `CompositorApp`: the new `Button(session.visibilityTitle)` and
  `Button(session.selectedClippingTitle)` passed a `String` (verbatim); now
  wrapped in `localizedString` at the display site.
- `NativeLayerList`: the new export menu title, visibility/clipping titles and
  the two conversion items are now localized at display; the
  `visibilityTitle` / `selectedClippingTitle` properties stay English so the
  new tests remain valid.
- `ProjectController`: the layer-export save/open panels, the folder prompt,
  both replace warnings and both "nothing to export" alerts are now localized,
  with `%lld` / `%@` format strings instead of interpolation.
- `LayersPanel`: the new footer menus use `localizedName`.
- `FilterSheet`: all new controls and help strings have catalog entries.
- `ProjectStore`: format 21's `reduceNoise` is optional, so versions 1–20 still
  decode; the PNG premultiply change is behavioural, not a format change.
- `EditorSession`: the new `visibilityTitle` property stays English; displays
  localize it, and the undo step goes through the existing history localization.

`audit_strings.py` reports **0 UI literals not in the catalog** and **0
`control(...)` titles missing**. It still counts the empty-string key `""` as
lacking zh-Hans; that key is present in the 1.5.12 baseline too and is not a
regression from this round.

## 5 Localization and verification results

- Catalog: **1515 → 1559 keys (+44)**.
- New keys: Reduce Noise / Volumetric Light and their controls and help,
  Show Extras / Distances, Show Layers / Hide Layers, New filter layer,
  `Selection %lld × %lld px`, and the layer-export panel/alert strings.
- The `visibilityTitle` / `selectedClippingTitle` properties remain English;
  the four new English assertions in `LayerTests` and `LiveMaskTests` therefore
  pass unchanged.
- `xcrun swiftc -parse` on the 56 changed Swift files: all parsed (syntax only;
  the real check is the build).
- Release build: `BUILD SUCCEEDED`, exit 0. Product: **1.6.3 (62)**,
  `com.wonderassembly.compositor.cn`, ad-hoc signature, no Team ID.
- Full Debug test run:
  `xcrun xcresulttool get test-results summary` → **794 total, 794 passed,
  0 failed, 0 skipped**. The result bundle is
  `build-logs/1.6.3-tests.xcresult`.
- Release smoke: the DerivedData product stayed alive for 7 seconds, its main
  thread sampled in `ReceiveNextEventCommon` (3 hits), then quit cleanly.
- The compiled `zh-Hans.lproj` contains the new strings (体积光, 降噪, 保留细节,
  选区 %1$lld × %2$lld 像素, 导出多个图层为 PNG…).

## 6 Manual acceptance focus

Not yet installed, tagged or pushed. Before replacing the installed 1.5.12:

1. Volumetric Light: first run downloads the depth model (online); offline
   falls back without a crash; Extract Depth produces a depth layer; colour
   picker samples on the canvas; every control and help text is Chinese.
2. Reduce Noise: the filter and the adjustment layer; save/reopen a project and
   confirm the settings survive; project format is 21.
3. Layer export: one layer, several layers, trimmed pixels, transparent pixels,
   hidden and grouped layers, names with `/` and `:`, and the replace prompt.
4. Multi-selection: visibility, clipping and 16/8-bit conversion each as one
   undo step.
5. Old `.comp` files open in 1.6.3; a 1.6.3 save is rejected by 1.5.12 as
   expected.
6. Camera RAW, PSD/PSB and import/export regressions; the T text-layer icon and
   the font display names.
7. After installing: version / build / Bundle ID / signature, then a second
   smoke test.
