# v1.5.12 conflict resolution

Round: 1.5.11 → 1.5.12, done by hand on 2026-10-28 after the updater (V2.2.1)
rolled the merge back on two content conflicts.

## Where the official source came from

- Upstream tag `v1.5.12` = `fe0a146d1a94476bbe68fb634ae9c31224eabced` (`git ls-remote`
  through Clash on 127.0.0.1:7897 — the sandbox proxy still 502s on `git`).
- Source: `https://codeload.github.com/robbietilton/Compositor/tar.gz/refs/tags/v1.5.12`,
  sha256 `37460a5b97c6d0c1409b7848b352fc13448351bec262d7edc016cf31457bfca5`, 4.1 MB.
- Synthetic snapshot commit **`9f77fe2`**, parent = the v1.5.11 snapshot `02daaea`.
  **Not** the real upstream tag commit — the ancestry chain is built from tarballs,
  as it has been since 1.5.7.

### Version gaps

Checked `git ls-remote --tags upstream` before starting: 1.5.11 → 1.5.12 with
nothing in between. Unlike last round (which silently carried 1.5.10), this one
is a single release.

### Why the updater rolled back

Two content conflicts — `project.pbxproj` and `ColorPalette.swift`. A genuine
conflict, not the `APP_PATCH_FAILED` ordering bug from 1.5.9 (that one trips on
`CompositorApp.swift`, and this round merged that file cleanly — it is not even
in upstream's changed list). The rollback was clean: HEAD back at `3cc2563`,
no `MERGE_HEAD`, `snapshot-tag` still `v1.5.11`, `last-conflicts.txt` matches
what the manual merge hit.

## What upstream v1.5.12 brings

One feature, ten files, +662/−24.

| Area | Change |
|---|---|
| Rim Light (new) | `Document/RimLight.swift` + `Rendering/MetalRimLight.swift`: up to three lights behind the subject that catch its edges, each with colour, angle, strength, width and choke, plus one Glow that hazes the light into the air around it |
| Subject mask | `SubjectRemoval.subjectMask(_:)` exposes Vision's raw mask, which Rim Light lights |
| 16-bit path | `FilterKind.rimLight` joins `runsAtSixteenBits` — one GPU pass on the layer's 16-bit pixels instead of three through `DeepLayer.run` |
| Filter sheet | `rimLightControls`: per-light heading, colour well, remove button, Add Light; and a "Finding the subject…" line while the first preview waits on Vision |
| Colour picker | `ColorPickerTarget.rimLight(index:)`; the dither titles lose their "Dither" qualifier |
| Project format | **Unchanged at 20** — see below |
| Tests | `RimLightTests.swift`, 132 lines |

### Why the format version did not move

`RimLightSettings` is `Equatable, Sendable` — **not `Codable`**, and not in
`FilterLayerSettings`, so it never reaches `.comp`. This is the same situation
`LensEffectSettings` was in before 1.5.9: the type lives only in the live filter
state, so upstream could add `var rimLight = RimLightSettings()` to
`FilterSettings` without a migration. `ProjectManifest.current` stays at 20 and
old projects open untouched.

Contrast with 1.5.9, where `LensEffectSettings` **became** Codable and needed
`decodeIfPresent` + a defaulting `init(from:)`. The rule does not change:
**look at whether the type is Codable before deciding whether a field change
needs a version bump.**

## The two conflicts

### `Compositor.xcodeproj/project.pbxproj` (two identical blocks, Debug and Release)

Upstream bumped `MARKETING_VERSION` to 1.5.12 and `CURRENT_PROJECT_VERSION` to
58, and its copy still carries the official bundle ID. Took the version numbers,
kept `com.wonderassembly.compositor.cn` in both blocks.

Signing sentinels re-verified afterwards on the App target, Debug and Release:
`CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`,
`ENABLE_HARDENED_RUNTIME = NO`. The `DEVELOPMENT_TEAM = 3E4X3B9Z9T` at lines 319
and 386 belongs to the tests and uitests targets and has been the baseline since
1.4.7 — not a regression.

Upstream's 24-line pbxproj diff is version numbers only: the three new files
land through `PBXFileSystemSynchronizedRootGroup`, so there are no new
`PBXBuildFile` / `PBXFileReference` entries to reconcile.

### `Compositor/Document/ColorPalette.swift` (`ColorPickerTarget.title`)

Two things happened in the same switch: upstream added `.rimLight(index:)` and
shortened the dither branches from "Color Picker (Dither Light Color)" to
"Color Picker (Light Color)". Took both, and wrapped every branch in
`localizedString` as before.

The light number is the one place a plain interpolation would have broken:

```swift
case .rimLight(let index): return String(format: localizedString("Color Picker (Light %lld)"), Int64(index + 1))
```

`localizedString("Color Picker (Light \(index + 1))")` compiles and looks fine,
but it produces a different key per light, so the catalog can never hold the
translation. The format string keeps one key.

Also note `.effect(let kind)` keeps our `kind.localizedName` rather than
upstream's `kind.rawValue` — that branch has been localised since 1.5.9 and the
conflict was the usual "our display layer against their behaviour".

## Auto-merged files that needed checking

`FilterSheet.swift`, `Filters.swift`, `SubjectRemoval.swift` merged cleanly.
Verified after the merge:

- `localizedString` count in `FilterSheet.swift`: 9 before, 9 after — no
  localization was silently dropped (1.5.7 and 1.5.9 both lost some this way).
- No `-` line in `git diff HEAD` for those three files removes a
  `localizedString` call.
- `control("Choke", …)` reaches the screen through
  `Text(verbatim: localizedString(title))`, so it needed a catalog entry — and
  the audit's sink regex cannot see it, because that line holds no `Text(` or
  `.help(`. Found by listing the new `control(` calls.
- Rim Light appears in the Filter menu automatically: the menu iterates
  `FilterKind.allCases` filtered by `isImageAdjustment`, and `rimLight` is not
  an image adjustment.
- No switch over `AdjustmentKind` needs a `.rimLight` case — Rim Light is a
  filter only, never an adjustment layer.

## Localization: 1502 → 1515 (+15, −2)

| Key | zh-Hans |
|---|---|
| `Rim Light` | 轮廓光 |
| `Choke` | 收缩 |
| `Light %lld` | 光源 %lld |
| `Add Light` | 添加光源 |
| `Choose this light's color` | 选择此光源的颜色 |
| `Remove this light` | 移除此光源 |
| `How far the light wraps around the subject's edges` | 光线环绕主体边缘的范围 |
| `How the light ends on the inside: …` | 光线在主体内侧的收尾方式：数值低时从边缘柔和淡出，数值高时保持明亮并干脆收住 |
| `Let the lights glow in the air around the subject, …` | 让光线在主体周围的空气中发光，与背景融为一体 |
| `Light the subject from another side as well` | 再从另一侧为对象打光 |
| `Where the light comes from, behind the subject: …` | 光线来自主体后方的哪个方向：0° 在右侧，90° 在上方 |
| `Finding the subject…` | 正在查找主体… |
| `Color Picker (Light %lld)` | 拾色器（光源 %lld） |
| `Color Picker (Light Color)` | 拾色器（亮色） |
| `Color Picker (Dark Color)` | 拾色器（暗色） |

Removed, because upstream renamed them and nothing else spells them:
`Color Picker (Dither Light Color)`, `Color Picker (Dither Dark Color)`.

`Glow` / `Angle` / `Strength` / `Width` already had entries (辉光 / 角度 / 强度 /
宽度), so `rimLightControls` only needed `Choke` from its slider row.

Deliberately **not** translated, checked this round: everything in
`RimLight.swift` and `MetalRimLight.swift` that looks like a string is a Core
Image filter name (`CIColorMatrix`, `CIDivideBlendMode`) or a Metal function
name (`rimLight`, `rimCombine`). Neither reaches the UI.

## Old-project compatibility

- `ProjectManifest.current` still 20 — no bump, no migration.
- Rim Light settings are session state, never persisted, so a project saved with
  Rim Light applied keeps only the rasterised result, exactly like any other
  filter.
- A project saved by 1.5.12 opens in 1.5.11 and earlier.

## Verification

| Step | Result |
|---|---|
| `xcrun swiftc -parse` on all seven touched Swift files | clean |
| Release build | `** BUILD SUCCEEDED **` |
| Full test suite | `** TEST SUCCEEDED **`, **752 / 752 passed**, 0 failed, 0 skipped (1.5.11 was 745, +7) |
| Release smoke test | process alive after 7 s; `sample` shows the main thread in `ReceiveNextEventCommon` |
| Installed build | `/Applications/Compositor-CN.app` = 1.5.12 / 58 / `.cn` / adhoc / no Team ID; starts and idles |
| Built `zh-Hans.lproj/Localizable.strings` | 轮廓光 / 收缩 / 光源 %lld / 添加光源 / 正在查找主体… / 拾色器（光源 %lld）/ 拾色器（亮色）/ 拾色器（暗色） all present; the two old Dither keys gone |
| Localization audit | 0 UI literals missing from the catalog; 1515 keys, only the pre-existing `""` placeholder lacks zh-Hans |
| Sparkle | `grep -rn "updater.start()\|checkForUpdates()\|startUpdater()\|SUFeedURL"` → nothing |
| Upstream deletions | none this round (`git diff --name-status` has no `D` lines), so no removed-symbol sweep needed |

## Manual acceptance focus

1. 滤镜 → 轮廓光…：第一次预览出现「正在查找主体…」，之后三个滑杆（角度/强度/宽度/收缩）与「辉光」都生效。
2. 「添加光源」加到第三个后按钮消失；「移除此光源」在只剩一个光源时不显示。
3. 每个光源的色块点开是「拾色器（光源 1）」，取消后颜色回到打开前。
4. 抖动滤镜的两端颜色，拾色器标题现在是「拾色器（亮色）」/「拾色器（暗色）」。
5. 打开 1.5.11 存的项目，确认格式 20 仍能读、滤镜菜单顺序未乱。
