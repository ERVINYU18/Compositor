# v1.6.4 conflict resolution

Round: 1.6.3 → 1.6.4, merged by hand on 2026-11-06. This is an incremental
release; the updater hit the same content conflicts and rolled back cleanly.

## 1 Where the official source came from

- Upstream tag `v1.6.4` = `f2add91afe7a63d789cf096cca34b797c4c0f0f7`
  (`git ls-remote --tags upstream` through Clash on 127.0.0.1:7897).
- Source: `https://codeload.github.com/robbietilton/Compositor/tar.gz/refs/tags/v1.6.4`,
  sha256 `e1365ed8aff15eaa3297bd31c8b17012c6daa4ff3f0d2c75bf1b526617410777`, 4.2 MB.
- Synthetic snapshot commit **`4eed49a`**, parent = the v1.6.3 snapshot
  `7b0a388`. **Not** the real upstream tag commit — the ancestry chain is built
  from tarballs.
- Merge commit **`e427c2c`**, parents `99f111a` (the Chinese release commit)
  and `4eed49a`. The snapshot branch is an ancestor of HEAD.
- Version/build after the merge: **1.6.4 / 63**. Bundle ID remains
  `com.wonderassembly.compositor.cn`.

### Version gaps

Checked before starting: 1.6.3 → 1.6.4, nothing in between.

## 2 What upstream changed

18 files, `+368 / -236`.

| Area | Change |
|---|---|
| Selection | Expand, Contract and Feather share one Size box (1–500, default 5) and three icon buttons; Feather is additive; Expand/Contract use mitered joins so corners stay square; the status bar shows the selection's feather |
| Colour palette | Reset and Swap become two buttons below the colours; a new `ColorSwatch` is shared with the filter panels; Reset's help is new |
| Tool headers | `ToolHeaderStyle` gains a shared pill and control layout; Brush, Shape, Type, Transform, Color Picker, Effects and Filter sheets adopt it |
| Tests | New feather assertions and selection tests |

No new source files; Xcode's synchronized folder groups mean no project-file
entries were needed beyond the version/build numbers.

## 3 Every conflict, and which side won

Six paths conflicted, exactly as the pre-merge simulation predicted. The
updater hit the same six and rolled back at 09:45; its transaction backup
branch is `backup-cn-v2-20261106-094508`.

### `Compositor.xcodeproj/project.pbxproj`

Upstream changed only the version and build number. **Took 1.6.4 / 63**, kept
the `.cn` bundle ID and the app target's four signing settings
(`CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`,
`DEVELOPMENT_TEAM = ""`, `ENABLE_HARDENED_RUNTIME = NO` in Debug and Release).

### `Compositor/ContentView.swift`

Upstream appended the selection's feather to the status bar with a raw string;
the Chinese branch had the localized selection size. **Kept the localized size**
and appended the feather through `String(format: localizedString(" · Feather %lld px"), …)`.

### `Compositor/UI/ColorPaletteControls.swift`

Upstream moved the swatches and the Reset/Swap buttons into a new layout; the
Chinese branch had localized the swatch label. **Took the upstream layout and
kept `localizedString(background ? "Background color" : "Foreground color")`.**
The new reset help key was added; `Reset colors` already exists.

### `Compositor/UI/EffectsSheet.swift`

Upstream moved the slider width into the shared header style; the Chinese
branch had localized the text field. **Took the upstream slider layout and kept
`TextField(localizedString(title), …)`.**

### `Compositor/UI/FilterSheet.swift`

Upstream replaced the local swatch drawing with the shared `ColorSwatch`; the
Chinese branch had `localizedTitle`. **Took the new body and kept the localized
title.**

### `Compositor/UI/LassoControls.swift`

Upstream replaced the three separate Expand/Contract/Feather controls with one
Size box and a three-icon pill. **Took the upstream controls**, localized the
icon accessibility labels and help
(`localizedString(operation.rawValue)` and the existing
`"%@ the selection by this many pixels"` format), and added the new
`"How many pixels to expand, contract or feather the selection by"` key.

## 4 Automatically merged files: spot checks

The other six files that both sides touched merged cleanly: `EditorSession`,
`BrushControls`, `ColorPickerSheet`, `ShapeControls`, `TransformInspector` and
`TypeControls`. Their `localizedString` counts are unchanged (for example
`EffectsSheet` 4, `FilterSheet` 9, `TransformInspector` 3, `TypeControls` 4);
no localization call was lost. `Selection.swift`, `ToolHeaderStyle.swift`,
`ToolRail.swift` and the tests came only from upstream.

`audit_strings.py` reports **0 UI literals not in the catalog**. It still counts
the empty-string key `""` as lacking zh-Hans; that key is present in earlier
baselines too and is not a regression.

## 5 Localization and verification results

- Catalog: **1559 → 1562 keys (+3)**:
  - `How many pixels to expand, contract or feather the selection by`
  - ` · Feather %lld px`
  - `Reset colors to black and white (D)`
- `operation.rawValue` is no longer passed raw to accessibility/help paths.
- `xcrun swiftc -parse` on the 16 changed Swift files: all parsed (syntax only;
  the real check is the build).
- Release build: `BUILD SUCCEEDED`. Product: **1.6.4 (63)**,
  `com.wonderassembly.compositor.cn`, ad-hoc signature, no Team ID.
- Full Debug test run:
  `xcrun xcresulttool get test-results summary` → **798 total, 798 passed,
  0 failed, 0 skipped**.
- Release smoke: the DerivedData product stayed alive for 7 seconds, its main
  thread sampled in `ReceiveNextEventCommon`, then quit cleanly.
- The compiled `zh-Hans.lproj` contains the new strings (羽化 %lld 像素,
  扩展、收缩或羽化选区时的像素数, 重置为黑白 (D)).
- Installed on 2026-11-06 after backing up 1.6.3 to
  `.Compositor-CN-Backups/pre-1.6.4-install-20261106-100349/`. The installed app
  reports **1.6.4 (63)**, ad-hoc, no Team ID, and passed the installed smoke.
  The user reported manual acceptance passed.

## 6 Release

- Release tag: `v1.6.4-cn`, on the commit that carries this record.
- `compositor-cn.snapshot-tag` is set to `v1.6.4`; the snapshot branch
  `compositor-upstream-snapshot` is `4eed49a` and is an ancestor of HEAD.
- Archive: `.Compositor-CN-Backups/post-1.6.4-cn-<timestamp>/` and its iCloud
  mirror, each verified with `shasum -c`.
- The branch and tag are pushed after this record; see the archive's
  `STATE--*.txt` for the final commit and test numbers.

## 7 Manual acceptance focus

The user's acceptance pass covered this round. Keep these areas in mind for the
next regression:

1. Selection Size box plus Expand/Contract/Feather icons; feather accumulates
   and shows in the status bar.
2. Colour palette Reset/Swap layout and the Chinese help strings.
3. Brush, Shape, Type, Transform, Color Picker, Effects and Filter headers.
4. Old `.comp` projects, PSD/PSB, Camera RAW, import/export.
