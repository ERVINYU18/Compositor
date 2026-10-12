# Compositor-CN 1.4.9 merge conflict decisions

Baseline: Chinese adaptation adapt-compositor-1.4.1 at a44ccbc (tag v1.4.7-cn).
Official snapshot: v1.4.9, tag commit 0ab3ff5 — 33 commits after v1.4.7 (no v1.4.8 tag was published).
Merge commit: d9a237c.
Merge conflicts: 9 files, 15 hunks.

The official v1.4.9 changes in this range: WebP import, a Camera Raw rework, the Navigator
minimap, Export As (PNG/JPEG/PDF), a Scanlines filter, and new project-tab close behaviour.

Note on how this merge happened: Compositor-CN Updater V2.2 attempted it first and hit the same
nine conflicts, then rolled back transactionally (HEAD, MERGE_HEAD, worktree, snapshot tag and
snapshot branch all restored). The merge was then completed by hand from that clean state.

## Resolutions

| File | Official 1.4.9 change | Existing Chinese customization | Resolution |
|---|---|---|---|
| Compositor.xcodeproj/project.pbxproj | Marketing version 1.4.9; official bundle ID com.wonderassembly.compositor; DEVELOPMENT_TEAM 3E4X3B9Z9T; GENERATE_INFOPLIST_FILE added. | App targets use com.wonderassembly.compositor.cn; team is empty so the build stays ad-hoc. | Took the official version number, kept the CN bundle ID, kept DEVELOPMENT_TEAM empty. Verified after merge: CODE_SIGN_IDENTITY "-", CODE_SIGN_STYLE Manual, ENABLE_HARDENED_RUNTIME NO, all intact. The four remaining official team IDs sit in the test targets and match the 1.4.7 baseline line-for-line — not a regression. |
| Compositor/CompositorApp.swift | Adds a CommandGroup with a "Check for Updates…" item driven by Sparkle. | No updater menu; the official update entry must stay dead. | Dropped the block entirely. |
| Compositor/IO/CompositorApplicationDelegate.swift | Starts the Sparkle updater one second after launch. | Same reason. | Dropped. The updater is a lazy var and nothing calls start(), so the entry point stays dead. |
| Compositor/Document/ColorPalette.swift | Replaces localized picker titles with plain strings and kind.rawValue. | Window titles are localized because AppKit does not localize them. | Kept the Chinese localized cases. |
| Compositor/IO/ImageFileDrop.swift | Adds WebP to the list of supported formats in the drop failure message. | The message already goes through localizedString(). | Kept the localized call and added WebP to the key's wording. |
| Compositor/IO/ImageImporter.swift | Adds WebP to the unsupported-format message; drops the PSB mention. | PSB was added by this branch — neither official 1.4.7 nor 1.4.9 mentions it. | Kept PSB (our shipped wording) and added WebP on top. |
| Compositor/IO/ProjectController.swift | Replaces the per-format save panels with a savePanel(for:) helper; deletes exportJPEG, which the new Export As flow replaces. | Titles, prompts and the unsaved-changes alert are localized. | Adopted the official structure and removed exportJPEG (verified zero references remained); localized the new helper's "Export <format>" and "Untitled" strings and kept the localized alert. |
| Compositor/UI/JPEGExportSheet.swift → Compositor/UI/ExportAsSheet.swift | Renamed and rewritten: PNG/JPEG/PDF, size, scale and page controls. | The old JPEG sheet was localized. | Took the official rewrite; every prompt goes back through localizedString(). |
| Compositor/UI/ProjectTabs.swift | The only tab, when still blank, no longer shows a close button. | Close help and accessibility labels are localized. | Kept the official behaviour; localized the help and accessibility labels. |

Additional dynamic UI fixes in this merge:
- DitherColors was rendered with Text($0.rawValue), so "Black & White", "Two Colors" and "Original"
  stayed English. Now resolved through the catalog. The static audit cannot see this pattern —
  it is a variable, not a literal.
- "Transparency kept · sRGB" in ExportAsSheet was a conditional literal and also invisible to the
  static audit. Now localized.

Localization: catalog grew from 1105 to 1141 keys, 0 missing zh-Hans. The static audit's open
items went from 28 to 2, and those two are the generic separators "·" and "×", which need no
translation.

Tests: 569 passed, 0 failed (the 1.4.7 baseline was 539).

## Future Updater rules

No merge rule was added to the formal Updater. The Sparkle blocks in CompositorApp and
CompositorApplicationDelegate recur every round, but their shape keeps changing, so they stay for
human review. The pbxproj conflict always needs the Release signing sentinels re-verified by hand.

One rule is worth stating explicitly for hand merges: finish the round by checking that
`compositor-cn.snapshot-tag` equals the new tag and that `compositor-upstream-snapshot` is an
ancestor of HEAD. Without both, the Updater will not short-circuit and will replay the whole
merge on its next run.
