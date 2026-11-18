# v1.6.13 conflict resolution

Round: 1.6.7 → 1.6.13, merged by hand on 2026-11-18. This round carries
**v1.6.8 through v1.6.12** (skipped upstream releases, merged together).

Merged because the updater (V2.4.0) correctly refused to guess at four
white-list-external conflicts. It rolled back cleanly and left
`last-conflicts.txt`; the actual merge was done by hand following the runbook.

## 1 Official source

- Upstream tag `v1.6.13` = `447cbc428bd46e56b476700d69234479eac6514e`
  (`git ls-remote --tags upstream`).
- Source: `https://codeload.github.com/robbietilton/Compositor/tar.gz/refs/tags/v1.6.13`,
  tarball sha256 `9676c89c2f492c06f516ec8e504713c5ca75a2d61713e289db8bb58940a71521`.
- Synthetic snapshot commit **`692f498`**, parent = the v1.6.7 snapshot
  `5060925`. Commit message states "NOT the real upstream tag commit".
- Version/build after the merge: **1.6.13 / 72**. Bundle ID remains
  `com.wonderassembly.compositor.cn`.
- Backup branch before merging: `backup-cn-1.6.13-merge-ff54bab`.
- Merge commit: `be49c5d`; localization key script commit: `b861774`.
- Tag sequence confirmed before starting: 1.6.7 → 1.6.8 → 1.6.9 → 1.6.10 →
  1.6.11 → 1.6.12 → 1.6.13. Six versions compressed into this one round.

## 2 What upstream 1.6.7 → 1.6.13 brings

36 files, +2972 / -219. Notable:

- **PSD export**: new `Compositor/IO/PSD/PSDWriter.swift`, format option in
  Export As, a "Changes" summary row.
- **Shape tool**: stroke colour/width picker, line dash/cap controls, corner
  radius + smooth corners.
- **Rotation cursor**: rewritten from a fixed `NSCursor` constant to an
  angle-dependent `rotationCursor(angle:)` with 16 cached variants.
- **Layer row drag-and-drop**: new `LayerDropForwarder.swift`;
  `NativeLayerList.swift` +435 lines.
- New tests: `LayerRowDragTests.swift`, `PSDExportTests.swift`, plus additions
  to Shape/ColorPicker/GPU/MagicWand/Transform suites. `@Test` declarations
  809 → 838.

## 3 Conflicts and their resolution

The updater's white list covers only `project.pbxproj`, `CompositorApp.swift`,
`BlendModePicker.swift`, `Localizable.xcstrings`. The other four files conflicted
this round and could not be auto-resolved — that is why the updater stopped.

Principle applied throughout: **display layer keeps Chinese, behaviour layer
keeps upstream**. No "all ours" / "all theirs".

| File | Decision | Why |
|---|---|---|
| `Compositor.xcodeproj/project.pbxproj` (2 blocks) | `MARKETING_VERSION` → 1.6.13; Bundle ID kept `.cn` | Behaviour/version from upstream, distribution identity from us. Verified after: signing four elements intact in App Debug+Release (`-`/Manual/empty/NO), tests/uitests `DEVELOPMENT_TEAM=3E4X3B9Z9T` untouched (6 sites), `.cn` ID count 2, official bare ID count 0, Sparkle still disabled. |
| `Compositor/Document/ColorPalette.swift` | Kept all `localizedString(...)` titles; added upstream's new `.shapeFill` / `.shapeStroke` cases, also localized | Display layer. Upstream used bare English literals; taking them would show English in the colour picker. |
| `Compositor/Rendering/EditorCanvas.swift` | Took upstream in full | Behaviour layer. Call sites (lines 1825/2888) now call `rotationCursor(angle:)`; keeping the old `rotationCursor` constant would not compile. Upstream implementation draws with Core Graphics and carries no user-facing string. |
| `Compositor/UI/ColorPickerSheet.swift` | Took upstream's `focused` / `onSubmit` / `channelValue` changes; kept our ternary `accessibilityLabel(localizedString(...))` | Behaviour from upstream; the ternary result is a `String` (verbatim path) so it must be explicitly localized. Other `.accessibilityLabel("literal")` calls stay bare by project convention (automatic catalog lookup). |
| `Compositor/UI/ExportAsSheet.swift` (2 blocks) | Added upstream's PSD summary and format hint as localized strings; kept existing Chinese branches | Display layer. Upstream's string-interpolation help text is a localization anti-pattern; replaced with two complete catalog keys selected by condition. |

## 4 Auto-merged files — spot checks

- **Upstream-removed symbols**: checked the deletion side of the snapshot diff
  for `func/var/let/struct/enum/class` names; nothing our branch references was
  removed without a replacement.
- **`localizedString` stripped by auto-merge**: the only two removals were in
  `ExportAsSheet.swift`, both replaced in the conflict resolution above with
  new Chinese keys (PSD lines). No other UI file lost localization.
- **New upstream files** — `PSDWriter.swift`, `LayerDropForwarder.swift` —
  are picked up by Xcode 16's folder-synchronised groups; no pbxproj edits
  needed.
- All five edited Swift files plus every changed Swift file pass
  `xcrun swiftc -parse`. Full compile correctness is proven by the Release
  build below, not by the parse check alone.

## 5 Localization

- Catalog: **1566 → 1580 keys** (+14). Script `tools/localization/add_1_6_13_keys.py`
  follows the established convention (backup, byte-identical re-serialisation
  guard, append-only, conflict-marker guard). Backup:
  `tools/localization/backups/Localizable.xcstrings.pre-1.6.13-20261118-143333.json`.
- New keys: PSD export (Changes, format summary, two "Other formats" hints),
  shape tool (fill/next-line/selected-line colour, stroke colour, stroke help,
  dash help, cap help, corner radius help), and the two colour-picker titles.
- `audit_strings.py`: **0 UI literals missing from catalog**; one `Text(verbatim:)`
  literal = letter T (intentional); one "key lacking zh-Hans" = baseline empty
  key, not a gap.
- `audit_keys.py`: **0 `LocalizedStringKey` gaps, 0 ternary gaps**.
- Manual blind-spot sweeps (required by AGENTS.md §4.7): ternary-carried help
  strings in `ShapeControls` were confirmed covered by catalog keys; AppKit
  setters clean; `rawValue` usages are either already localized or unit symbols
  (`px`/`in`/`cm`/`mm`, data names — deliberately untranslated).
- **A correction made during the round**: an initial pass wrapped
  `ShapeControls`' `.help("literal")` calls in `localizedString(...)`. That was
  wrong for this project — `.help("literal")` takes `LocalizedStringKey` and
  looks the catalog up automatically (78 such calls already existed and were
  accepted). The over-eager edit was reverted; the gaps were fixed by adding
  catalog keys instead.

## 6 Build, test, install

Run by the user in a real terminal via `构建验证装机-1.6.13.sh` (xcodebuild
cannot start inside a WorkBuddy process — nested `sandbox-exec` refused).

- Full test: **838 passed / 0 failed**, top-level `totalTestCount = 838`
  (`xcresulttool` on `build-logs/1.6.13-tests.xcresult`; device-level 962 is
  the inflated figure and was not used). Cross-check: `@Test` declarations in
  `CompositorTests/` = 838, matching.
- Release build: `BUILD SUCCEEDED`. Product **1.6.13 (72)**,
  `com.wonderassembly.compositor.cn`.
- Product `codesign -v --deep --strict`: passed. `Contents/MacOS/` contains
  only `Compositor` — no stale debug dylibs.
- Product smoke: stayed alive ≥ 7 s.
- Install: old 1.6.7 archived to
  `.Compositor-CN-Backups/pre-1.6.13-install-20261118-143603/`; new version
  installed with `ditto`, `codesign -v --deep --strict` passed, launched OK.
- `git config compositor-cn.snapshot-tag` set to `v1.6.13`; snapshot branch is
  an ancestor of HEAD — the updater's four "already up to date" conditions
  are now all satisfied for the next run.

## 7 Why the updater could not finish this round

V2.4.0's gate is a white list, not a semantic resolver. Four files fell outside
it, so it rolled back and wrote `last-conflicts.txt` — correct behaviour, since
those files are behaviour/display layer and a wrong guess would be a silent
error. What was missing is the stage-2 handoff/resume protocol (structured
handoff package + resume mode), so the updater could stop but had no path to
continue. That is a planned next piece of work, not a regression of V2.4.0.
The updater also has no state for "sources merged but app not installed", so
it cannot take over this round mid-way; from v1.6.14 onward, with sources and
app both at v1.6.13, it returns to its normal path.

## 8 Manual acceptance focus

1. Shape tool: new stroke colour picker, width, dash/cap, corner radius and
   smooth corners — all labels and help text in Chinese.
2. Export As: PSD format present, layer/folder/mask note in Chinese, "Changes"
   summary readable.
3. Colour picker: fill/stroke titles show Chinese.
4. Rotation cursor changes with angle (new upstream behaviour).
5. No visible English anywhere in the UI, especially the newly added help text.
