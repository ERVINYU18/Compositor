# Compositor-CN 1.3.3 merge notes

Base: `adapt-compositor-1.2.9` at `7d2bc61` (includes the 1.2.9 Chinese adaptation). Official snapshot: `compositor-upstream-snapshot` at `3f17534` (1.3.3, build 30). The 1.3.3 app target keeps bundle ID `com.wonderassembly.compositor.cn`.

## Conflict decisions

| File | Official 1.3.3 change | Existing CN behavior | Resolution |
| --- | --- | --- | --- |
| `Compositor.xcodeproj/project.pbxproj` | Advances marketing version/build to 1.3.3/30 and uses the official bundle ID. | The app target uses `com.wonderassembly.compositor.cn`. | Keep 1.3.3/build 30 in both app configurations and restore the CN bundle ID. Test and UI-test bundle IDs remain their own identifiers. |
| `Compositor/Document/ColorPalette.swift` | Adds Dither light/dark color-picker targets. | Existing picker titles translate text, effect, palette, gradient-map, and vignette targets; effect names use localized names. | Keep all CN lookups and add translated Dither light/dark target keys. |
| `Compositor/UI/CameraRawColorControls.swift` | Adds draggable numeric labels for curve and mixer controls. | Curve and mixer labels and the composed mixer help string are explicitly localized. | Keep the translations and help text, and add upstream `.scrubbable` bindings/ranges. |
| `Compositor/UI/CameraRawDetailOpticsControls.swift` | Adds draggable labels for Detail and Optics controls. | Dynamic labels use explicit lookup and localized text-field prompts. | Keep localized labels/prompts and add the upstream bindings, sensitivity, and ranges. |
| `Compositor/UI/CameraRawGeometryCalibrationControls.swift` | Adds draggable labels for Geometry and Calibration controls. | Dynamic labels and process summaries are explicitly localized. | Keep localized labels and add upstream scrubbing, including the calibration tone range. |
| `Compositor/UI/EffectsSheet.swift` | Adds drag-to-adjust numeric labels. | Effect titles are translated explicitly. | Keep the localized title and add the upstream scrubbable binding/range. |
| `Compositor/UI/FilterSheet.swift` | Adds label-width measurement, scrubbing, colored tracks, double-click reset, and an exact-value field. | Dynamic control titles and text-field prompts are explicitly localized. | Keep the full 1.3.3 interaction and track behavior, localize dynamic titles/prompts, and format the dynamic reset tooltip through the String Catalog. Dither enum names now use `localizedName`; its AppKit color-picker title and tooltips also use explicit catalog lookups. |
| `CompositorTests/TypeToolTests.swift` | Adds an explicit assertion for click-to-baseline placement and updates the clipping fixture to a canvas-corner origin. | The 1.2.9 test checked the resulting raster layer's actual origin and used that origin when placing the clipping fill. | Keep the new click-origin assertion and the prior actual-layer-origin assertion. Use the official corner-origin fixture while positioning the fill from the resulting source layer, preserving both 1.3.3 placement coverage and the 1.2.9 raster-bound check. |

## Updater follow-up assessment

No V2.2 rules were changed. A narrowly validated project-file rule could preserve the CN app bundle ID while accepting a supported upstream marketing version/build, but it must identify only the app target and verify the resulting settings. The Camera Raw and Effects conflicts are candidates for a future structural rule only if it can prove the localized label and upstream scrubbing binding refer to the same control. FilterSheet, ColorPalette, and TypeToolTests require semantic edits, so they remain stop-and-review cases. Unrecognized conflict paths continue to stop and roll back.
