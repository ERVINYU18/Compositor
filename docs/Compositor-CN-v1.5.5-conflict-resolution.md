# v1.5.5 conflict resolution

Merged 2026-10-22 as `417f660` (parents `0e7382f` Chinese + `bd97cab` official snapshot).

## Where the official source came from

`github.com`'s git endpoint was unreachable from this session (the sandbox proxy answers
CONNECT with 502; `api.github.com` answers normally), so the snapshot is built from the
codeload tarball of `refs/tags/v1.5.5` (sha256
`38c8b7f968037c058acf72b4f5fda885794762b94fd1d5f6bdf555bea49b08bc`).

* Official tag `v1.5.5` is really commit `b31ea029762ecb782699df971e1412168602a44d`
  (2026-10-21, "Channel Pack writes its PNG itself, so color under transparent pixels
  survives on macOS 26").
* `bd97cab` is therefore **a synthetic commit**: its tree is the official tag's, but its
  parent is the previous official snapshot (`v1.5.3` = `554104c`). Ancestry is synthetic by
  one hop. The previous round that needed this trick was v1.4.10.

What upstream v1.5.5 brings: PDF import with its own password-protected error, Channel Pack
export for game textures, a rewritten font picker (a searchable panel replaces the pop-up
menu), pen-pressure brushes, the dispersion filter, and stroke caps.

## The seven conflicts

Every one keeps the new upstream behaviour and the Chinese copy. Nothing was resolved with
"all ours" or "all theirs".

### 1. `Compositor.xcodeproj/project.pbxproj`

Two hunks, both `MARKETING_VERSION` + `PRODUCT_BUNDLE_IDENTIFIER`:

* version follows upstream: **1.5.5**, build **51**;
* bundle id stays **`com.wonderassembly.compositor.cn`**.

Checked right after the merge, as every round requires: the Compositor target's Release
config still has `CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`,
`DEVELOPMENT_TEAM = ""`, `ENABLE_HARDENED_RUNTIME = NO`. The upstream
`DEVELOPMENT_TEAM = 3E4X3B9Z9T` still sits in the two test targets only (4 places, same as
the 1.4.7/1.4.9 baseline) — left alone on purpose.

### 2. `Compositor/CompositorApp.swift`

* **Undo / Redo**: upstream now forwards `undo:`/`redo:` to the key window when it is an
  `NSSavePanel`, so the panel's own name field undoes its typing. Kept that forwarding, and
  kept this branch's `localizedString("Undo %@")` / `localizedHistoryAction(...)` titles.
* **New Adjustment Layer menu**: upstream split `AdjustmentKind.allCases` into
  `imageAdjustments` (the Image menu's) and `filters` (the Filter menu's). Kept the split,
  and kept `kind.localizedName` for both lists — upstream's `kind.rawValue` would have put
  untranslated enum names on screen. The second list is outside the conflict hunk and was
  changed for the same reason.

### 3. `Compositor/IO/ImageFileDrop.swift`

Upstream added PDF to the list of readable formats. Kept the new wording, still wrapped in
`localizedString()`.

### 4. `Compositor/IO/ImageImporter.swift`

* PDF joins the readable formats; this branch's **PSB** (its own addition) stays in the list,
  so the message mentions both.
* New `ImageImportError.locked` — "This PDF is password-protected…" — added, localized.
* `tooLarge` keeps this branch's `String(format: localizedString(...))` form rather than
  upstream's interpolation, so both numbers can be formatted.

### 5. `Compositor/UI/ExportAsSheet.swift`

* New `channelPack` row in the format note, localized like the rows around it.
* The "other formats" help now mentions Channel Pack; kept the two localized variants
  (with and without EXR) instead of upstream's interpolated string.

### 6. `Compositor/UI/LayersPanel.swift`

Same `imageAdjustments` / `filters` split as the app menu, with `localizedName`.

### 7. `Compositor/UI/TypeControls.swift`

The largest change. Upstream **replaced the pop-up menu with a searchable font panel**
(`FontListPanel`): the coordinator's `menuNeedsUpdate`, `menuWillOpen`, `menuDidClose`,
`menu(_:willHighlight:)` and `choose(_:)` are gone, replaced by `FixedWidthPopUpButton.open`
and `Coordinator.open()`.

This branch's old delegate methods were therefore dropped — keeping them would have left a
menu nobody fills, since the coordinator no longer conforms to `NSMenuDelegate`. What the
branch keeps:

* `setAccessibilityLabel(localizedString("Font"))`;
* `multiple = localizedString("(Multiple)")`;
* **`displayName`**: this branch's `styledName(_:displayName:)` and `makeStyledName(_:fontName:)`
  still draw each face's *display* name (loaded by PostScript name). Upstream's call site
  passes one argument, so it was widened to
  `Self.styledName($0, displayName: TypeFontPicker.displayName(for: $0))` — otherwise the
  panel would list PostScript names.

## Localization

25 new catalog keys (1346 → 1371), no key left without zh-Hans, and no UI literal left out
of the catalog:

* the font panel's own AppKit strings — `placeholderString = "Search Fonts"` and
  `accessibilityDescription: "Clear search"` — which the audit's sinks do not cover, because
  they are set on AppKit objects rather than passed to a SwiftUI sink;
* PDF import: the readable-formats list, the password-protected error, the drop message;
* Channel Pack: the format note, the other-formats help, `Channel Pack` itself;
* pen pressure: the two help strings and the two accessibility labels;
* stroke caps: `Cap`, the dash/dot help, the cap help;
* dispersion: direction, distance, smear, linear/radial, move-the-center, `Split to Layers`,
  the long channel-split help, and `Split Channels` (a history action name, which the undo
  menu shows through `localizedHistoryAction`);
* `Import…`.

## Still to do

Build, test and accept — none of which can run from the agent sandbox (`xcodebuild` fails at
SwiftPM resolution). The official tests added this round
(`ChannelPackTests`, `FilterLayerTests`, `FontMenuFacesTests`, `PDFImportTests`,
`PSDArtboardTests`, `PenPressureTests`) were read for hardcoded English assertions and none
were found, so they should not need the adaptation the v1.5.3 round needed.
