# v1.5.6 conflict resolution

Merged 2026-10-23 as `286bfad` (parents `d34fa2d` Chinese + `cdfc9ba` official snapshot).

## Where the official source came from

The codeload tarball of `refs/tags/v1.5.6` (sha256
`dfb9c1e98b4a4ff3df969b9dbfa57f9945490a15f2c5d36dc61afcdee36378cb`).

* Official tag `v1.5.6` is commit `68b248ae9aa610f149411b0a29c6e024c380945f`.
* `cdfc9ba` is therefore **a synthetic commit**, exactly as in the v1.4.10 and v1.5.5
  rounds: its tree is the official tag's, but its parent is the previous official
  snapshot (`v1.5.5` = `bd97cab`). Ancestry is synthetic by one hop.
* The updater itself stopped on these conflicts and rolled back cleanly (13 paths,
  listed in `~/Library/Application Support/Compositor-CN-Updater/last-conflicts.txt`),
  so the merge was finished by hand here.

What upstream v1.5.6 brings — 54 files, +2716/−346:

* **Animated GIF**: `GIFDecoder`, `GIFExporter`, `GIFAnimation`, `GIFFrameTiming`,
  `GIFPreviewPlayback`, `EditorSession+GIF`, and the `GIFTimeline` strip under the
  canvas (play/pause, per-frame delays, duplicate and delete a frame).
* **Export As › GIF**: loop Forever/Once, keep-transparent toggle, its own matte
  colour, "Up to 256 colors · sRGB", and an encoding progress line.
* **Layers panel**: a search field that replaces the panel title, plus a type filter
  (Images / Shapes / Text / Folders / Adjustments / Selected) — `LayerSearchControls`.
* **`UI/ToolRail.swift`**: the tool rail moved out of `ContentView`.
* A GIF depth tag in the layer list, and a GIF preview button in Export As.

## The thirteen conflicts

Every one keeps the new upstream behaviour and the Chinese copy. Nothing was resolved
with "all ours" or "all theirs".

### 1. `Compositor.xcodeproj/project.pbxproj`

Version follows upstream: **1.5.6**. Bundle id stays
**`com.wonderassembly.compositor.cn`**. Checked right after the merge, as every round
requires: the Compositor target's Debug and Release still have
`CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`,
`ENABLE_HARDENED_RUNTIME = NO`. Upstream's `DEVELOPMENT_TEAM = 3E4X3B9Z9T` still sits
in the test targets only (4 places, same as the 1.4.7/1.4.9/1.5.x baseline) — left
alone on purpose.

### 2. `Compositor/CompositorApp.swift`

Keeps the Chinese `localizedString("Delete %@")` and `selectedEffect!.kind.localizedName`;
takes upstream's `session.selectedMask(for: $0)`.

### 3. `Compositor/ContentView.swift`

Upstream extracted the whole tool rail into `Compositor/UI/ToolRail.swift`
(`IndicatorlessScrollView`, `ColorPaletteControls`, the 56 pt width layout), and
`editorStack` now just uses `ToolRail(session: session)`. The Chinese `toolRail` block
is deleted rather than kept: leaving it would duplicate the rail. Nothing else in it
was Chinese-only, so nothing is lost.

### 4. `Compositor/Document/EditorSession+Brush.swift`

`selectedMask(for: layer)?.isEnabled` from upstream, Chinese `localizedString(...)` kept.

### 5. `Compositor/Document/Filters.swift`

Takes upstream's `layerByEditingPixels(...)`; keeps `beginEdit(edit.kind.localizedName)`.

### 6. `Compositor/Document/ProjectWorkspace.swift`

Keeps `String(format: localizedString(...))` for the copy errors and adds upstream's GIF
branch: `localizedString("The copied GIFs exceed this project’s animation memory limit.")`.

### 7. `Compositor/Document/SmudgeLiquify.swift`

`let active = activeLayer` from upstream; Chinese `localizedString(...)` kept.

### 8. `Compositor/IO/CompositorApplicationDelegate.swift`

**Upstream brought its Sparkle start-up back** (`try self?.updater.start()`,
`checkForUpdates()`). Deleted again, with the same comment as previous rounds: the
Chinese build has no update entry. Verified afterwards that no source calls
`updater.start()` and `Config/Info.plist` has no `SUFeedURL` / `SUPublicEDKey` /
`SUEnableAutomaticChecks`. `runsTests` and the rest of the delegate are untouched —
`UpdateCheckTests` depends on `runsTests`.

### 9. `Compositor/IO/ImageFileDrop.swift`

GIF joins the readable formats; Chinese `localizedString(...)` kept.

### 10. `Compositor/IO/ImageImporter.swift`

GIF joins the readable formats and `case .tooManyFrames` is new upstream:

```swift
case .unsupported: localizedString("Choose a JPEG, PNG, GIF, HEIC, HEIF, TIFF, WebP, PDF, Photoshop (PSD), or Photoshop Large Document (PSB) file.")
case .tooManyFrames:
    String(format: localizedString("This animation has more than %@ frames, which exceeds the current timeline limit."),
           GIFTimelineLimits.maxFrames.formatted())
```

PSB support stays.

### 11. `Compositor/IO/ProjectStore.swift`

Upstream's version message now names four version numbers, so the Chinese format string
follows: `"...versions %lld–%lld, 27, and %lld."` with
`ProjectManifest.upstreamVersions.lowerBound`, `.upperBound` and `.current`.

### 12. `Compositor/UI/ExportAsSheet.swift` — three hunks

* The background swatch takes upstream's GIF matte:
  `DialogColorSwatch(title: localizedString("Export Background"), color: format == .gif ? gifMatte : matte, session: session)`.
* The line under the format buttons gains `format == .gif ? localizedString("Up to 256 colors · sRGB")`.
* The "More formats" help becomes three-way localized, with GIF named in both branches.

### 13. `Compositor/UI/NativeLayerList.swift` — three hunks

* `deleteTitle` follows upstream's `session.selectedMask(for: layer) != nil`, keeping
  `localizedString("Delete Mask")` — the tests look the menu item up by that call, so
  the wrapper must stay.
* The folder chevron keeps upstream's "filters list folders opened" rule
  (`enabled && !session.isFilteringLayers`, chevron down while filtering) with
  `localizedString("Expand or collapse folder")` as its accessibility description.
* The depth tag gains upstream's GIF tooltip
  (`localizedString("Animated GIF: select it to show its frames under the canvas")`)
  while `depthTag.text` keeps `layer.depthLabel.map { localizedString($0) }` — the
  label now reads `GIF`, `HDR` or `16-Bit`.

## Localization

Catalog: **1371 → 1431 keys**. `02-localization/add_1_5_6_keys.py` appended 60 entries.

`audit_strings.py` reports **0 UI literals missing from the catalog**. Because the
audit's sink regex cannot see enum-backed labels, ternaries or AppKit setters, a wider
sweep of every literal in `Compositor/` was run as well; it turned up these extra gaps,
all fixed in the same pass:

* `LayerType.titleKey` / `filterLabel` (Images, Shapes, Folders, Adjustments, and the
  six "Filter to …" VoiceOver labels);
* `isPlaying ? "Pause" : "Play"` in the GIF timeline and in the Export As preview;
* `field.placeholderString = "Search Layers"` (now `localizedString`);
* `gifSummary` and the export progress line, which are `String` values shown through
  `Text(String)` — that initialiser does **not** localize, so both now go through
  `String(format: localizedString(...))`;
* `GIFExportError`'s two descriptions and `EditorSession.importError`'s
  "Couldn’t read GIF frame …" — `LocalizedError.errorDescription` is returned verbatim
  by `localizedDescription`, so the literals had to be wrapped;
* the GIF edits' history names ("Change GIF Delays", "Duplicate GIF Frame",
  "Delete GIF Frame(s)"), which the Edit and History menus show;
* two older leaks found on the way: the PDF page-size line
  (`"%@ × %@ in at %lld DPI"`) and the Channel Pack channel help.

Deliberately **not** translated:

* `"Generic CMYK Profile"` / `"Embedded CMYK Profile"` — ColorSync profile names.
  `CMYK.generic` finds macOS's profile by that exact string, so translating it would
  break profile lookup.
* `GIFDelayMode`'s raw values (`"Frame delay"`, `"Same for all"`) — Codable storage
  values, never shown.

`audit_strings.py`'s one remaining "key lacking zh-Hans" is the empty key, whose
translation is the empty string: the script tests the value's truthiness, so it reports
a false positive. The JSON has
`{"localizations": {"zh-Hans": {"stringUnit": {"state": "translated", "value": ""}}}}`.

## Tests

Four new test files come with this version: `GIFLayerTests`, `GIFPreviewPlaybackTests`,
`ToolRailTests`, `UpdateCheckTests`. Full suite: **707 passing, 0 failing**
(`xcrun xcresulttool get test-results summary`, 1.5.5 was 687 — +20).
