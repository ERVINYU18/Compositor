# v1.5.7 conflict resolution

Merged 2026-10-24 as `7a70268` (parents `5d9ea7a` Chinese + `2104c0f` official snapshot).

## Where the official source came from

The codeload tarball of `refs/tags/v1.5.7` (sha256
`bd2bbbcf7ecc7dd326a8fedbd149000ecb35653df7252b8ca4a7ad35b1816749`).

* Official tag `v1.5.7` is commit `9537736da6c324b948cdcba24adf74760498ea14`
  (published 2026-10-23 18:06 UTC, read through `api.github.com` — the git endpoint
  still answers `CONNECT tunnel failed, response 502` in this environment).
* `2104c0f` is therefore **a synthetic commit**, as in the v1.4.10 / v1.5.5 / v1.5.6
  rounds: its tree is the official tag's, its parent is the previous official snapshot
  (`v1.5.6` = `cdfc9ba`). Ancestry is synthetic by one hop.
* The updater stopped on this version too, but **not on a text conflict** — it merged
  `project.pbxproj`'s conflict, then its dynamic-English check found two new
  `Text($0.rawValue)` pickers in `FilterSheet.swift` and rolled the whole transaction
  back. That rollback was clean; the merge was redone by hand here.

What upstream v1.5.7 brings — 13 files, +787/−44:

* **Lens Effects** (`FilterKind.lensEffects`), one filter with five effects, each with
  its own controls: Anamorphic Flare, Starburst, Mist, Prism, Bokeh.
  New `Document/LensEffects.swift` (settings + Core Image path) and
  `Rendering/MetalBokeh.swift` (the Bokeh discs, on the GPU canvas).
* **GIF playback** now runs through `GIFPreviewPlayback.play(durations:startingAt:clock:)`,
  and `GIFSource` keeps one `CGImageSource` open (`withReader`) instead of rebuilding a
  reader per frame — a partial frame otherwise replays from the first one, which is too
  slow to play.
* **The GIF timeline's delay label** became `<delays> · Original`, where `<delays>` is
  one number or `shortest–longest`.
* `README.md` and `appcast.xml` follow upstream untouched (the latter is the official
  feed and is inert for the CN build — no `SUFeedURL`).

## The one conflict

### `Compositor.xcodeproj/project.pbxproj` (two identical blocks, Debug and Release)

Version follows upstream: **1.5.7 / build 53**. Bundle id stays
**`com.wonderassembly.compositor.cn`**. Checked right after the merge, as every round
requires: the Compositor target's Debug and Release still have
`CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`,
`ENABLE_HARDENED_RUNTIME = NO`. Upstream's `DEVELOPMENT_TEAM = 3E4X3B9Z9T` still sits in
the test targets only (4 places, same as the baseline) — left alone on purpose.

`LensEffects.swift`, `MetalBokeh.swift` and `LensEffectsTests.swift` need no file
entries: the project uses `PBXFileSystemSynchronizedRootGroup`, so anything inside
`Compositor/` and `CompositorTests/` is picked up automatically.

## What the updater's dynamic-English check caught

Its `DynamicEnglish.txt` listed exactly two lines, and it was right to stop:

```
Compositor/UI/FilterSheet.swift:420: ForEach(BokehShape.allCases, id: \.self) { Text($0.rawValue).tag($0) }
Compositor/UI/FilterSheet.swift:367: ForEach(LensEffect.allCases, id: \.self) { Text($0.rawValue).tag($0) }
```

`Text(String)` is the verbatim initialiser, so those pickers would have shown
"Anamorphic Flare" and "Cat's Eye" in a Chinese UI. Both now read
`Text(verbatim: $0.localizedName)` — the same form every other enum-backed picker in
this repo uses (`BrushControls`, `CameraRawColorControls`, …). The raw values stay
English; only the catalog supplies Chinese, so nothing that might ever be persisted
changes.

The rest of `lensEffectsControls` was left as upstream wrote it, because SwiftUI
localises those forms on its own: `Text("Effect")`, `Picker("Points", …)` and
`.help(…)` all take a `LocalizedStringKey`, and `control("Length", …)` passes its title
through `localizedString(title)` inside the helper.

## Localization

1431 → **1465** catalog keys (34 new), written by
`02-localization/add_1_5_7_keys.py`:

* the filter and its labels: `Lens Effects`, `Effect`, `Points`, `Length`, `Copies`,
  `Reach`, `Brightness`, `Ring`;
* the five effect raw values and the four aperture shapes;
* sixteen `.help` strings;
* `%@ · Original` for the timeline's delay label. Note the old bare `Original` key
  already existed and means "原始颜色" (a colour picker's original), which is why the
  new composite key matters — the timeline no longer reads that one.

`audit_strings.py` reports **0 UI literals missing from the catalog**. A separate sweep
of the touched files (enum-backed labels, ternaries, AppKit setters) is clean too, and a
targeted check of every literal inside `lensEffectsControls` finds Chinese for all of
them except `\($0)`, the star-point count, which is a bare number.

`LensEffectsTests` asserts pixels and `isIdentity`, never a display name, so the
localisation cannot break it.

## Tests

One new test file (`LensEffectsTests`, 138 lines) and 55 more lines in
`GIFPreviewPlaybackTests`. Measured after the merge: **720 passing, 0 failing**
(1.5.6 was 707, so upstream added 13 cases).
