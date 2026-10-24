# v1.5.8 conflict resolution

Merged 2026-10-24 as `3a5f648` (parents `9569124` Chinese + `d76e31b` official snapshot).

## Where the official source came from

The codeload tarball of `refs/tags/v1.5.8` (sha256
`6d516ec515909b81296e25a8702cf970edb3eab0b64a2874379f5adadf638b64`).

* Official tag `v1.5.8` is commit `8adf15e3b9e421dc1f2e0de28cb190d1fb5b48e2`
  (published 2026-10-24 04:48 UTC, read through `api.github.com` — the git endpoint
  still answers `CONNECT tunnel failed, response 502` in this environment).
* `d76e31b` is therefore **a synthetic commit**, as in the v1.4.10 / v1.5.5 / v1.5.6 /
  v1.5.7 rounds: its tree is the official tag's, its parent is the previous official
  snapshot (`v1.5.7` = `2104c0f`). Ancestry is synthetic by one hop.
* The updater (V2.2.1) stopped on a **real content conflict** this time, not on its
  localization gates: it merged `project.pbxproj`'s conflict, then hit one in
  `ProjectStore.swift` and rolled back. The rollback was clean — HEAD was still
  `9569124`, the working tree untouched, `compositor-cn.snapshot-tag` still `v1.5.7`.

What upstream v1.5.8 brings — 8 commits, 7 files, +156/−79:

* **Lens Effects' Prism is reworked.** `prismSpread` ("Reach") is gone. In its place:
  `prismBlur` ("Blur", 0–100, softens the copies more the farther they're pushed) and
  `prismBothWays` (a "Direction" segmented picker: One Way / Both Ways). The rendering
  path changed with it — copies are now stepped along a line from the picture itself
  (`result = light`, built farthest-first) instead of being masked to a gradient band
  from one edge, so a copy shows wherever it is brighter than what's behind it. Prism
  also applies at Offset 0 now (`isIdentity` no longer treats `prismOffset == 0` as a
  no-op), which is what its preview always showed.
* **Threshold runs to 100.** Past 95 it stops being "how bright" and becomes "how big
  and solid": `LensOptics.sources()` blurs the above-0.95 mask, measures the frame's
  own peak with `CIAreaMaximum`, and keeps only spots solid enough at that level — down
  to the strongest one or two lights. `highlights()` was split so the tone-curve mask
  is reusable (`brightness(_:above:)`).
* **`ProjectManifest` accepts every format version again.** `upstreamVersions = 1...14`
  and the `supported` set built from it are replaced by a single
  `static let supported = Set(1...current).union([27])`. Formats 15 and 16 — what
  1.5.4 and 1.5.5 wrote — had been locked out.
* `appcast.xml` follows upstream untouched (official feed, inert for the CN build: no
  `SUFeedURL`, `startUpdater()` never called).

## The two conflicts

### `Compositor.xcodeproj/project.pbxproj` (two identical blocks, Debug and Release)

Version follows upstream: **1.5.8 / build 54**. Bundle id stays
**`com.wonderassembly.compositor.cn`**. Checked right after the merge, as every round
requires: the Compositor target's Debug and Release still have
`CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`,
`ENABLE_HARDENED_RUNTIME = NO`. Upstream's `DEVELOPMENT_TEAM = 3E4X3B9Z9T` still sits in
the test targets only (same as the baseline) — left alone on purpose.

### `Compositor/IO/ProjectStore.swift` (`ProjectError.errorDescription`)

This is the interesting one. In an earlier round we rewrote every case of
`errorDescription` to go through `localizedString()`, and the `.version` case reads the
supported range straight off the manifest:

```swift
String(
    format: localizedString("This project uses format version %lld. This app supports versions %lld–%lld, 27, and %lld."),
    Int64(version),
    Int64(ProjectManifest.upstreamVersions.lowerBound),   // ← this property no longer exists
    Int64(ProjectManifest.upstreamVersions.upperBound),
    Int64(ProjectManifest.current)
)
```

Upstream deleted `upstreamVersions` outright, so this would not have compiled. Resolved by
keeping our localized shape and taking upstream's new wording, which needs two
placeholders instead of four:

```swift
case .version(let version):
    String(
        format: localizedString("This project uses format version %lld. This app supports versions 1–%lld and 27."),
        Int64(version),
        Int64(ProjectManifest.current)
    )
```

The other four cases are unchanged from our version. `grep -rn upstreamVersions` across
`Compositor/`, `CompositorTests/` and `CompositorUITests/` comes back empty — nothing else
referenced it. `ProjectManifest`'s header (the new `supported` line and its comment) took
upstream's version verbatim; it was not in conflict.

## What auto-merged, and what that required checking

Upstream touched five files we also care about; only two conflicted.

* **`Compositor/UI/FilterSheet.swift`** — auto-merged, and both of the
  `Text(verbatim: $0.localizedName)` fixes from v1.5.7 survived (`LensEffect` at line 367,
  `BokehShape` at 420). Upstream's edits here are additive: the two Threshold ranges
  widened to `50...100`, both Threshold help texts gained a clause, Prism's Angle help was
  reworded, "Reach" was replaced by "Blur", and the Direction `HStack` is new.
* **`Compositor/Document/LensEffects.swift`** — byte-identical to upstream's; we had
  never touched it.
* **`CompositorTests/LensEffectsTests.swift`** — upstream's `prismGhostsACopyAtItsEdge`
  became `prismGhostsASharpCopy` (same count), plus `prismBothWaysEchoesOnEachSide` and
  `prismWithoutOffsetStillApplies`. We had never touched this file.
* **`CompositorTests/ProjectTests.swift`** — auto-merged. Our two local tests
  (`version9ProjectsRemainReadable`, `resavingAProjectKeepsQuickLookPreviewAndDropsFinderThumbnail`)
  are still there alongside upstream's new `projectsFromEarlierReleasesStillOpen`.
  Nothing in the file asserts on error text — the version-rejection test only checks
  `version == 42` — so the reworded format string needed no test change.
* **`appcast.xml`** — follows upstream. Inert.

Worth recording for future rounds: `LensEffectSettings` is `Equatable, Sendable` but **not
`Codable`**, and does not appear in the saved project. That is why upstream could rename
`prismSpread` to `prismBlur`/`prismBothWays` without bumping the format version (still
17). Before assuming a settings change is archive-compatible, check whether the struct is
actually persisted.

## Localization

Catalog 1465 → 1470 keys (+9, −4), via `02-localization/add_1_5_8_keys.py`.

Added:

| Key | zh-Hans |
|---|---|
| `Direction` | 方向 |
| `One Way` | 单向 |
| `Both Ways` | 双向 |
| `Which way the copies step` | 重影偏移的方向 |
| `Soften the copies, more the farther they're pushed` | 柔化重影，偏移越远越柔和 |
| `Copies to one side of the picture, or out to both` | 重影只出现在画面一侧，或向两侧同时延伸 |
| `How bright a light has to be to flare; near 100, only the biggest, brightest spots` | 光线要多亮才会产生光晕；接近 100 时只保留最大最亮的光源 |
| `How bright a light has to be to sparkle; near 100, only the biggest, brightest spots` | 光线要多亮才会产生星芒；接近 100 时只保留最大最亮的光源 |
| `This project uses format version %lld. This app supports versions 1–%lld and 27.` | 此项目使用的格式版本为 %lld。本 App 支持版本 1–%lld 和 27。 |

Removed (each verified to have no remaining source reference before deletion):

* `Reach` / `延伸` — Prism's slider is gone.
* `How far into the frame the copies show from that edge`
* `Which way it's pushed, toward the edge the prism sits at` — Angle's old help.
* `This project uses format version %lld. This app supports versions %lld–%lld, 27, and %lld.`

"Blur" → 模糊 already existed (RGB Split's), so the new Prism slider picked it up for free.

The catalog round-trip check passed (re-serialising reproduces the original bytes exactly,
no trailing newline), and the backup is
`02-localization/backups/Localizable.xcstrings.20261024-171510.bak`.

A full literal sweep of the three touched UI/IO files found no remaining gap. The hits it
reported are all non-translatable: `.exr`, `manifest.json`, `Preview.jpg`, `images`,
`QuickLook`, `mmapped file changed` in `ProjectStore.swift`, and Core Image filter names
(`CIBlendWithAlphaMask`, `CILanczosScaleTransform`, `CIMorphologyRectangleMaximum`, …) in
`LensEffects.swift`.

## Verification

| Check | Result |
|---|---|
| Full test suite | **723 passed, 0 failed** (`Test-Compositor-2026.10.24_17-16-34-+0800.xcresult`) |
| Release build | succeeded |
| Product | 1.5.8 / build 54, `com.wonderassembly.compositor.cn`, `Signature=adhoc`, `TeamIdentifier=not set` |
| Hardened runtime | off — `CodeDirectory flags=0x2(adhoc)`, no `0x10000` |
| `SUFeedURL` | absent |
| Launch smoke (product) | process alive past 6 s, no crash report |
| Launch smoke (installed) | `/Applications/Compositor-CN.app` alive past 6 s, no crash report |
| Rollback point | `~/Desktop/.Compositor-CN-Backups/pre-1.5.8-install-20261024-172711` (1.5.7 / 53, 32 MB, `codesign -v --strict` clean) |
| Previous app | moved to Trash as `Compositor-CN-1.5.7-53-*.app`, recoverable |

723 = 720 (v1.5.7) + 3: `prismBothWaysEchoesOnEachSide`, `prismWithoutOffsetStillApplies`,
`projectsFromEarlierReleasesStillOpen`.

One runtime warning is emitted, unrelated to this merge and present before it:
`FloatingPanelTests.swift` — a User-interactive thread waiting on a Default-QoS thread
(priority inversion).

## Manual acceptance focus

1. **Prism** — the whole panel changed. Check the Blur slider softens copies (more so as
   Offset grows), One Way / Both Ways flips copies to both sides, and Offset 0 still
   applies fringing instead of doing nothing.
2. **Threshold at 96–100** — on a night shot with several bright lights, the top of the
   range should keep only the strongest one or two, not just dim everything.
3. **Old projects** — open something saved by 1.5.4 or 1.5.5 (format 15 or 16). This was
   the point of the release; the error message for a genuinely too-new project should now
   read 此项目使用的格式版本为 42。本 App 支持版本 1–17 和 27。
