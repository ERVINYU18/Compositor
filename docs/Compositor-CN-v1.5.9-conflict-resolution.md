# v1.5.9 conflict resolution

Merged 2026-10-26 as `54ec684` (parents `77560d6` Chinese + `88ef9c1` official snapshot).

## Where the official source came from

The codeload tarball of `refs/tags/v1.5.9` (sha256
`58302f522441e4b3f51f616d43b4d8d2638e79672de8951fd29e5b0d6f01f76a`).

* Official tag `v1.5.9` is commit `efc06ffdf6f93606e59a1f2220fcd64a5d4e0ade`
  (read through `api.github.com` — the git endpoint still answers
  `CONNECT tunnel failed, response 502` in this environment).
* `88ef9c1` is therefore **a synthetic commit**, as in the v1.4.10 / v1.5.5 / v1.5.6 /
  v1.5.7 / v1.5.8 rounds: its tree is the official tag's, its parent is the previous
  official snapshot (`v1.5.8` = `d76e31b`). Ancestry is synthetic by one hop.
* The updater (V2.2.1) did **not** stop on a content conflict this time. It stopped on
  `APP_PATCH_FAILED` — a new failure mode, see below.

### Why the updater failed: the CN patch script validates too early

`update.command` patches `CompositorApp.swift` after merging, and for a file that git
reported as conflicted it then asserts six "the Chinese rules really came back"
patterns (`Check for Updates…`, `Undo \(session.history.undoName)`, and four more). But
the file still held `<<<<<<<` markers at that point, so none of the patch's
search-and-replace steps could match, and all six patterns were still present:

```
APP_PATCH_FAILED: Check for Updates…, Undo \(session.history.undoName), Redo \(session.history.redoName), Button(kind.rawValue +
```

So the assert is correct in spirit but runs one step too early: **it should either be
skipped while conflict markers remain, or run only after the conflict is resolved.**
Nothing was written to `last-conflicts.txt` either (it still held the 2026-10-24 list),
because the script aborts before that. The rollback itself was clean: HEAD `77560d6`,
working tree untouched, `compositor-cn.snapshot-tag` still `v1.5.8`.

This is worth fixing in the updater before the next round — see "Follow-up" at the end.

## What upstream v1.5.9 brings — 9 commits, 26 files, +1100/−130

The largest round since the fork began, and the first one to bump the **project format
from 17 to 18**.

* **Vignette, Lens Effects and Tonal Contrast become adjustment layers.** `AdjustmentKind`
  gains `vignette`, `lensEffects`, `tonalContrast`, and `AdjustmentKind.filters` grows to
  nine entries. Their settings live in three new **optional** objects on
  `FilterLayerSettings` — `vignette: VignetteLayerSettings?`, `tonal: TonalLayerSettings?`,
  `lens: LensEffectSettings?` — with `resolvedVignette` / `resolvedTonal` falling back to
  defaults. `ProjectStore` writes 18 and, on load, rejects a layer that carries any of
  them unless `manifest.version >= 18`.
* **`LensEffect`, `BokehShape` and `LensEffectSettings` become `Codable`**, with a custom
  `init(from:)` that reads every field through `decodeIfPresent` and falls back to
  `Self()`'s default. So settings added in later releases never make an older file
  unreadable. This also means `LensEffectSettings` is no longer a non-persisted value
  type — the 1.5.7-era note "it's only `Equatable, Sendable`, so field renames can't
  break old projects" no longer applies to it.
* **The canvas caches each adjustment layer's result** (`AdjustmentSurface.swift`,
  `EditorCanvas.swift`) and only redoes the work when something under it, or about it,
  changes. Bokeh runs on the GPU (`MetalBokeh.swift`) without reading back.
* **RGB Split with blur runs in two passes** — streaks first, then spectrum — several
  times faster for the same look (`MetalDispersion.swift`).
* **Bokeh's Round, Hexagon and Oval discs share one weight table** computed once a
  frame; **Starburst** turns the picture once per direction and spreads each length's
  lights once for all three colors.
* **Lens Effects layers on the canvas now match Copy Merged and the export**, with
  matching angles and spike sizes (`side:` threaded through every `LensOptics` entry
  point so a partly-drawn layer measures itself against the whole picture).
* **The Filter menu splits in two** — filters that can also be adjustment layers (in
  that menu's order), a divider, then the rest — through a new shared
  `filterMenuItem(_:)` helper.
* New files: `Rendering/MetalFinishing.swift` (Vignette and Tonal Contrast kernels),
  `CompositorTests/AdjustmentCacheTests.swift`, `CompositorTests/AdjustmentPerformanceTests.swift`.

## The two conflicts

### `Compositor.xcodeproj/project.pbxproj` (two identical blocks, Debug and Release)

```diff
-				MARKETING_VERSION = 1.5.8;
-				PRODUCT_BUNDLE_IDENTIFIER = com.wonderassembly.compositor.cn;
+				MARKETING_VERSION = 1.5.9;
+				PRODUCT_BUNDLE_IDENTIFIER = com.wonderassembly.compositor;
```

**Took upstream's version, kept our bundle ID**: `MARKETING_VERSION = 1.5.9`,
`PRODUCT_BUNDLE_IDENTIFIER = com.wonderassembly.compositor.cn`. Upstream also moved
`CURRENT_PROJECT_VERSION` to 55.

Signing sentinels re-verified on the App target, both configurations:
`CODE_SIGN_IDENTITY = "-"` (2), `CODE_SIGN_STYLE = Manual` (2),
`DEVELOPMENT_TEAM = ""` (2), `ENABLE_HARDENED_RUNTIME = NO` (2). The
`DEVELOPMENT_TEAM = 3E4X3B9Z9T` at lines 319/386 is the pre-existing tests/uitests
baseline and was left alone.

`MetalFinishing.swift` needed no pbxproj entry: the project uses
`PBXFileSystemSynchronizedRootGroup`, so new files under `Compositor/` join their target
by folder. Verified by the fact that `MetalFinishing` appears zero times in the pbxproj
and the build still compiles its kernels.

### `Compositor/CompositorApp.swift` (the Filter menu)

Ours (one loop, already localized):

```swift
ForEach(FilterKind.allCases.filter { $0 != .contentAwareFill && !$0.isImageAdjustment }, id: \.self) { kind in
    Button(kind.localizedName + "…") { session.beginFilter(kind) }
        .disabled(!(kind == .vignette ? session.canVignette : session.canAdjustColors) || session.hueSaturation != nil)
}
```

Upstream (two loops, English, through a new helper):

```swift
// Those that can also be adjustment layers, in that menu's order, then the rest.
let layered = AdjustmentKind.filters.compactMap(\.filterKind)
let others = FilterKind.allCases.filter { $0 != .contentAwareFill && !$0.isImageAdjustment && !layered.contains($0) }
ForEach(layered, id: \.self) { filterMenuItem($0) }
Divider()
ForEach(others, id: \.self) { filterMenuItem($0) }
```

**Took upstream's structure, kept the Chinese display.** The split menu and the helper
are upstream behaviour; only the helper's label changed:

```swift
private func filterMenuItem(_ kind: FilterKind) -> some View {
    Button(kind.localizedName + "…") { session.beginFilter(kind) }   // upstream: Button("\(kind.rawValue)…")
        .disabled(!(kind == .vignette ? session.canVignette : session.canAdjustColors) || session.hueSaturation != nil)
}
```

Worth noting: upstream's own `Button("\(kind.rawValue)…")` is a `LocalizedStringKey`
interpolation, so it renders the English raw value. Left as-is it would have put
`Vignette…`, `Lens Effects…`, `Tonal Contrast…` into the Chinese menu.

## Auto-merged files that needed checking

| File | What to verify | Result |
|---|---|---|
| `Document/LayerAdjustment.swift` | our 2 `localizedName` uses survive | intact |
| `Document/LensEffects.swift` | no localizable strings (it's model code) | intact |
| `Document/Filters.swift` | our 3 `localizedName` uses | intact |
| `Document/AdjustmentEditing.swift` | our 1 `localizedName` use | intact |
| `IO/ProjectStore.swift` | our 5 `localizedString` uses, incl. the version error | intact |
| `Rendering/EditorCanvas.swift` | our 5 `localizedName` uses | intact |
| `Tests/FloatingPanelTests.swift` | no display strings | intact |

Every count matched HEAD exactly, so nothing was flattened by the auto-merge this round.

## Localization: 1470 → 1471 (+1, no removals)

`RGB Split` was the only real gap, and it is a **1.5.7 leftover**: both `FilterKind` and
`AdjustmentKind` spell it as a raw value and reach the screen through `localizedName`,
so it had been rendering in English for two releases. Now `RGB 分离`.

Checked and deliberately not translated:

* `Vignette` / `Lens Effects` / `Tonal Contrast` — already have zh-Hans from 1.5.7
  (晕影 / 镜头效果 / 色调对比度), because they were filter names before they became
  adjustment kinds.
* `Adjustment input` — the `ImportedImage` name for the scratch layer that feeds an
  adjustment's histogram. That layer never enters the manifest and never shows in the
  layer list.
* `Frame delay` / `Same for all` — `GIFFrameTiming` raw values; `GIFTimeline` builds its
  own millisecond and `· Original` labels.
* `Solid` / `Dotted` / `Dashed` / `Long Dash` — `ShapeLineStyle` raw values, used for dash
  patterns rather than menu titles.
* `CMYK Profiles` — a directory name on disk, matched exactly (translating it would break
  the lookup silently).
* `Drag to paint` / `Drag to erase` — substrings of one long `localizedString` key whose
  full text is already translated; the scanner flags the substring, not the key.

### Three raw-value displays fixed in `ExportAsSheet.swift`

Not new this round, but the updater's dynamic-English check (`Text($0.rawValue)`) would
have caught them next time and parked the merge:

* `ForEach([ExportFormat.jpeg, .png]…) { Text($0.rawValue) }` → `Text(verbatim: $0.localizedName)`
* `ForEach(others…) { Text($0.rawValue) }` → `Text(verbatim: $0.localizedName)`
* `Menu(chosen ? format.rawValue : "More")` → `Menu(chosen ? format.localizedName : localizedString("More"))`

The first two are behaviour-neutral: `ExportFormat`'s raw values are `PNG` / `JPEG` /
`TIFF` / `PDF` / `GIF` / `EXR`, and there are no catalog entries for them, so
`localizedName` returns them unchanged. The third is a real fix — `Menu`'s
`StringProtocol` overload does not consult the catalog, so "More" had been showing in
English even though the catalog has it as 更多.

## Old-project compatibility

Format 17 files must still open, because 1.5.8 wrote them.

* `FilterLayerSettings` has **no** custom `init(from:)`. Its three new members are
  `Optional`, and Swift's synthesized decoder reads optionals with `decodeIfPresent`, so
  a 17 file decodes them as `nil` and `resolvedVignette` / `resolvedTonal` supply
  defaults.
* `LensEffectSettings` is now `Codable` with an explicit `decodeIfPresent`-based
  `init(from:)`; a 17 file's lens settings (if any) decode field by field against
  `Self()`'s defaults.
* `ProjectStore`'s new v18 guard only fires for a layer that actually carries one of the
  new objects, so a 17 file cannot trip it.

## Verification

* `xcrun swiftc -parse` clean on all eight changed sources.
* Metal kernel names cross-checked: `vignette` and `tonalContrast` are defined in
  `MetalFinishing.swift`'s shader source and looked up by exactly those names in
  `library.makeFunction(name:)`.
* Full test suite: **734 passed / 0 failed** (`Test-Compositor-2026.10.26_09-52-49`),
  against 723 for 1.5.8. The +11 is upstream's: AdjustmentCacheTests 2,
  AdjustmentPerformanceTests 1, FilterLayerTests +4, GPUCanvasTests +4.
* One runtime warning, in `FloatingPanelTests.swift`: a user-interactive thread waiting
  on a default-QoS thread (priority inversion). It is in test code and predates this
  round.
* Release product: 1.5.9 / 55, `com.wonderassembly.compositor.cn`, `Signature=adhoc`,
  `CodeDirectory flags=0x2(adhoc)` (no hardened runtime), no `SUFeedURL`, 33 MB.
* Launch smoke: passed both on the Release product and after installing to
  `/Applications`.

## Manual acceptance focus

1. **New adjustment layers** — Vignette / Lens Effects / Tonal Contrast: add, adjust,
   save, reopen. These are the whole point of format 18.
2. **Canvas vs export** — upstream specifically fixed Lens Effects layers on the canvas
   not matching Copy Merged and the export. Compare on a night shot with several lights.
3. **A project saved by 1.5.8** (format 17) — the optional-field reasoning says it opens;
   this is where to prove it.

## Follow-up: the updater's premature assert

`update.command` should not assert the six Chinese patterns while the file still holds
conflict markers. Two options, both small:

* skip the assert when `"<<<<<<<" in s`, or
* move it after the conflict-resolution step.

Until that changes, any round where `CompositorApp.swift` conflicts will end in
`APP_PATCH_FAILED` instead of parking on `wip-cn-<version>-needs-localization`. The
rollback is safe, so this costs a round trip rather than data.
