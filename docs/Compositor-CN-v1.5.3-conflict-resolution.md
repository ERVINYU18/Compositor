# Compositor-CN 1.5.3 merge conflict decisions

Baseline: Chinese adaptation `adapt-compositor-1.4.1` at `aa07af4` (state after the v1.4.10-cn acceptance).
Official release: v1.5.3, upstream tag commit `554104cf1c2de844c1acbd60b4f7b422bd6ce7bd`.
Merge source: the real upstream tag — no synthetic snapshot this round.
Compositor-CN merge commit: `98a5fb13ca016fbc0e32aea53ed58b7b40844196` (parents `aa07af4` + `554104c`).
Follow-up commits: `29eae44` (catalog), `6429648` (numbered Untitled tabs in Chinese), `ff84b7c` (duplicate-enum fix).

## Source provenance

v1.4.10 merged a codeload tarball committed as synthetic snapshot `1fb57a2`, leaving an ancestry gap. This round fetched the real v1.5.3 tag: the merge parent is the actual upstream tag commit `554104c`. The updater's ancestry conditions are updated accordingly — `compositor-cn.snapshot-tag` moves from `v1.4.10` to `v1.5.3`, and `compositor-upstream-snapshot` moves from `1fb57a2` to `554104c` (both old locations stay reachable through `backup-snapshot-v1.4.10-pre-1.5.3-20261017`).

## Conflicts and resolutions

22 conflict paths: 13 Swift/test files (17 conflict blocks), `project.pbxproj`, `.github/workflows/verify.yml`, `appcast.xml`, and 6 AppIcon PNGs. `Localizable.xcstrings` merged automatically as a union of both sides' additions.

Policy, as in previous rounds: behavior follows upstream; the display layer keeps Chinese; a few blocks needed hand-written resolutions on top.

| File | Blocks | Official v1.5.3 change | Resolution |
|---|---|---|---|
| `Compositor/Document/Filters.swift` | 3 | Progressive Blur; unified `render(_:job:)` path | upstream |
| `Compositor/IO/ImageFileDrop.swift` | 1 | Accepted-format lists | Chinese message kept |
| `Compositor/IO/ImageImporter.swift` | 2 | Import paths and messages | Chinese messages kept, upstream logic |
| `Compositor/IO/PSD/PSDTypes.swift` | 1 | New CMYK strings | custom: upstream text, wrapped in `localizedString()` |
| `Compositor/IO/ProjectStore.swift` | 1 | Store internals | upstream |
| `Compositor/UI/ExportAsSheet.swift` | 1 | EXR/CMYK choices and captions | custom: upstream layout, Chinese format strings (`CMYK – %@`, EXR caption) |
| `Compositor/UI/FilterSheet.swift` | 1 | New filter row | upstream |
| `Compositor/UI/KeyboardShortcuts.swift` | 1 | Clear-a-shortcut row (`chord.isNone`) | custom: upstream logic, `localizedString()` kept on the display string |
| `Compositor/UI/LayerMaskMenu.swift` | 2 | CMYK proof / gamut-warning menu items | upstream blocks + post-pass wrapping 8 new strings in `localizedString()` |
| `Compositor/UI/LayersPanel.swift` | 1 | Adjustment list rows | upstream block + post-pass `Button(kind.localizedName)` |
| `Compositor/UI/NativeLayerList.swift` | 1 | 16-bit/HDR depth badges | custom: Chinese size line kept, new badge help strings wrapped in `localizedString()` |
| `Compositor/UI/RawDevelopSheet.swift` | 1 | Shadow controls | Chinese slider path kept |
| `CompositorTests/ImageImportTests.swift` | 1 | New expectations | upstream |

Non-Swift paths:

- `project.pbxproj`: version `1.5.3` / build `49`, CN bundle ID `com.wonderassembly.compositor.cn`. The upstream file overwrites the Release signing fixes easily, so they were re-checked after the merge: `CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`, `ENABLE_HARDENED_RUNTIME = NO`.
- `.github/workflows/verify.yml`, `appcast.xml`: upstream versions wholesale.
- AppIcon set: upstream re-encoded the six PNGs (visually identical); took upstream.
- `Localizable.xcstrings`: union merge, both sides' keys kept (+195 net).

## Merge follow-up fixes

- `ImageFolder` was declared twice in the merged tree (each side kept one declaration in a different file); the first build failed until the duplicate was removed in favor of the v1.5.3 declaration (`ff84b7c`).
- `6429648`: numbered Untitled documents show Chinese tab names (`未命名 2`, via `localizedUntitledName`).
- `29eae44`: +195 catalog entries for the strings v1.5.3 added.

## Localization audit

- Catalog: 1151 → **1346** keys; all keys resolve in zh-Hans (one empty-string extraction artifact resolves to empty).
- Four leak classes re-audited: AppKit literals (`NSMenuItem`, tooltips), runtime concatenation (converted to format strings such as `String(format: localizedString("CMYK – %@"), …)`), missing catalog entries, SF Symbol language variants (the text-layer badge remains the hand-drawn `T`).
- Display-layer additions this round: floating selection (浮动选区), pasted image (粘贴的图像), numbered Untitled names (未命名 N), PSD stroke/rasterize notices, crop-to-canvas notice, shortcut-editor titles (display only — persisted `title` ids stay English), history action names.
- Deliberately kept English: generated layer/folder names (`Layer/Folder N`), device and format presets, UpdateDriver (Sparkle) strings, ICC profile names as ColorSync reports them, numeric readouts. The letter `T` never localizes.

## Test adaptations this round

Two things changed in the test suite, both because the app localizes more, and because of a system window rule on this machine:

1. Assertions against localized copy (previously hard-coded English):
   - `CMYKTests`: a CMYK profile's `name` comes from `ColorSyncProfileCopyDescriptionString`, which the OS localizes (普通CMYK描述文件); the test now compares the embedded profile bytes (`.data`) instead of the display name.
   - `CropToCanvasImportTests`: two assertions read the crop notice through `localizedString()`; the negative substring check uses the full localized sentence so it cannot pass falsely.
   - `PSDRoundTripTests`: the omitted-stroke notice (`isn’t`, U+2019) and the rasterized-shape notice are read through `localizedString()`.

2. Window-position tests and the system's left window margin (Stage Manager):
   - `FloatingPanelTests/dockedPlacementLeavesTheSavedFilterPosition` and `ColorPickerTests/pickerReopensWhereItWasLastLeft` park a panel at the screen's left edge (x = 40) and assert it reopens exactly there. With Stage Manager enabled on this machine (`defaults read com.apple.WindowManager GloballyEnabled = 1`), a floating window parked below the stage margin is moved to x = 221 (this display's margin) inside `makeKeyAndOrderFront`; y is untouched, and the editor window — a plain `NSWindow` — is not affected. `constrainFrameRect` on an `NSPanel` maps any x < 221 to 221, independent of the editor window's position and of the app being active or not.
   - Activating the test host did not change the outcome under the xcodebuild runner, so the two tests park the panel at `screen.midX − 200` — well inside the stable area — instead of depending on activation.
   - Product code is unaffected: panels already hide on deactivate, so ordinary use never hits this margin. Diagnostic traces lived in `build-logs/probe-*.xcresult|log` (removed during round cleanup); the instrumentation diff and the raw probe trace are kept with the round's verification evidence in the project workspace (`01-merge-scene-evidence/1.5.3-window-margin-instrumentation.diff` and `1.5.3-window-margin-fpdebug.log`).

3. External-change timing (`ExternalChangeTests`): with 654 tests running side by side on this machine, the file-system notification can arrive later than the 4-second window the suite assumed. Both full runs of the merged suite failed `eventually { externalChanges.reloadCount == 1 }` under load (the test ran ~149 s versus ~7 s in isolation). The `eventually` default timeout in that file is now 20 s — the same adaptation family as the pending-state wait added in the v1.4.7 round. A passing path still returns on the first poll; a genuinely missing notification still fails, just later.

## Verification status

- Full suite (`xcodebuild ... test`, 2026-10-17): **654 tests, 654 passed, 0 failed, 0 skipped** — `build-logs/tests-1.5.3-run4.xcresult`. The first full runs after the merge had 7 failures (run2) and 1 failure (run3); they are exactly the ones fixed above.

## Release build and installation

- Zero-argument Release build: **BUILD SUCCEEDED** (`build-logs/release-1.5.3.log`). Product at `Build/Products/Release/Compositor.app`: version **1.5.3 / build 49**, bundle ID `com.wonderassembly.compositor.cn`, ad-hoc signature, TeamIdentifier not set, no official Sparkle keys in the Info.plist.
- Compiled `zh-Hans.lproj/Localizable.strings`: 1346 entries; spot checks (「保留比白色更亮的光 · 保留透明度」, the crop notice, the PSD stroke notice, 「无配置文件」) all present.
- Launch smoke test: product alive beyond 8 seconds; no Compositor crash report.
- Installed 2026-10-17: `/Applications/Compositor-CN.app` replaced with the 1.5.3 build after its launch check. The previous 1.4.10 / build 45 app was **moved** (not copied) to `~/Desktop/.Compositor-CN-Backups/pre-1.5.3-install-20261017-095910/Compositor-CN-1.4.10-previous.app` — rollback is a move back.
- Installed copy launch check: alive, then quit cleanly.

Manual acceptance: **pending** (user).

Next: manual acceptance, then the `v1.5.3-cn` tag, dual offline archive, snapshot reference update, and remote push.
