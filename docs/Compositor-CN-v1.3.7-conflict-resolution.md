# Compositor-CN 1.3.7 merge conflict decisions

Baseline: Chinese adaptation adapt-compositor-1.3.3 at 7d41d69.
Official snapshot: v1.3.7 tree 3b2b4ff8, tag commit 9e2894e.
Merge conflicts: 3 files.

## Resolutions

| File | Official 1.3.7 change | Existing Chinese customization | Resolution |
|---|---|---|---|
| Compositor.xcodeproj/project.pbxproj | Updates app marketing version/build to 1.3.7 (34), lowers deployment target to 26.0, restricts the app to arm64, and includes Xcode 27 settings. | The app target uses com.wonderassembly.compositor.cn; tests have separate identifiers. | Kept the official version, build, deployment target and architecture settings; retained the CN bundle ID only for the app targets. |
| Compositor/Document/ColorPalette.swift | Adds .dialog(title:) so a dialog can use the app color picker. | Existing target titles use Simplified Chinese; effect titles use localizedName rather than raw enum values. | Kept the Chinese cases, added .dialog, and formatted its title with the translated Color Picker (%@) key. Dialog labels are localized at their call sites before being passed in. |
| Compositor/IO/ProjectController.swift | Passes EditorSession into Canvas Size and JPEG Export so their custom color swatches use the app picker; adds Grid Settings and Quick Look saving. | AppKit sheet titles are localized. Canvas Size and JPEG Export had older initializer signatures. | Adopted the official session-based initializers and Quick Look save path; retained localized Canvas Size and JPEG Export titles and localized the Grid sheet title. |

Additional dynamic UI fixes in this merge:
- Grid preset/style labels resolve through localized names rather than showing rawValue.
- Color Range eyedropper accessibility labels use explicit translated labels.
- The mixed-font (Multiple) menu item is localized.
- Project tab close/add-to labels and the Levels histogram accessibility label use translated format strings.

## Future Updater rules

No merge rule was added to the formal Updater. The project-file conflict could be considered for a future rule only when the target block is identified unambiguously and post-merge checks verify the exact CN bundle ID, 1.3.x marketing version, build, deployment target and architecture. The ColorPalette and ProjectController conflicts depend on new enum cases, initializer changes and localization behavior; keep them for human review. Unknown files or shapes must continue to stop and roll back.
