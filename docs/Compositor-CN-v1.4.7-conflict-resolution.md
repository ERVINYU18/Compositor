# Compositor-CN 1.4.7 merge conflict decisions

Baseline: Chinese adaptation adapt-compositor-1.4.1 at 8cd93f1 (tag v1.4.5-cn).
Official snapshot: v1.4.7, tag commit 675d8a4 — 39 commits after v1.4.5.
Merge commit: 18d182c (tag v1.4.7-cn, later moved to a44ccbc).

Written after the fact, from the merge commit message and the repository. It records the
decisions that still matter; it does not attempt to reconstruct a file-by-file list that
was never written down.

## Scale, and why the number is fuzzy

The merge commit records 26 conflicting files with 69 hunks, resolved per hunk: 50 hunks
kept the Chinese side, 18 the upstream side, 1 was blank.

Replaying the same merge today with `git merge-tree --write-tree --name-only 8cd93f1 675d8a4`
reports 75 conflicting paths. The gap is explained by how this merge happened: it was
abandoned part-way through and resumed later, so 26 is the count recorded for the state
that was actually finished, while 75 is what a clean single-pass replay produces. Both come
from the same parents. **Take 75 as the size of the job if it ever has to be redone.**

One structural note worth keeping: `git merge-base 8cd93f1 675d8a4` is 9d5582d, a commit from
the Compositor 1.1.6 era. The Chinese branch was seeded by copying upstream sources rather
than by forking, so the two sides share almost no history. Every merge is effectively a
two-way reconciliation over a very old base, which is why the conflict surface is far larger
than the upstream change list would suggest.

## Decisions

| Area | Official 1.4.7 change | Existing Chinese customization | Resolution |
|---|---|---|---|
| Compositor/ContentView.swift | Adds a `canvasOnly` mode. | The Chinese build added `showsRulers`. | Kept both: upstream `canvasOnly` and the Chinese `showsRulers`. |
| Compositor/Document/EditorSession.swift | Adds `canvasOnly`. | Same, plus `showsRulers`, and `rawImporting` alongside `showsRawDevelop`. | Kept both pairs. |
| Compositor/IO/RawImporter.swift | Takes upstream `workingFormat` and `workingColorSpace`. | `useSoftwareRenderer` is pinned to false. | Kept false, took the upstream format and color space. |
| Config/Info.plist | Brings back four official Sparkle keys, including SUFeedURL pointing at robbietilton/Compositor. | The Chinese baseline has none, and the official updater is never started. | Dropped all four. |

Beyond the conflicts, 69 hunks were resolved per hunk rather than with a wholesale
ours/theirs. That is the rule, not an exception: the display layer keeps Chinese, the
behaviour layer follows upstream.

## Localization

The command palette (Compositor/UI/CommandPalette.swift, CommandPaletteView.swift) was new in
1.4.7 and entirely English. 31 zh-Hans keys were added.

Two decisions there are worth keeping:

- **Entries are localized when they are built, not when they are displayed.** The `id` stays
  English. Search ranks on `entry.title`, so localizing only at display time would leave every
  tool unsearchable for a Chinese typist.
- **Tool keys are composite: `Tool > <name>`.** Bare names collide. `Type` is already
  translated as the brush kind picker ("类型"), but the type tool must read "文字". The palette
  therefore uses `Type Tool`.
- The `skipped` set in CommandPaletteView is **bilingual**, because it matches menu item titles
  as they are currently displayed. Under zh-Hans those are 窗口 / 帮助 / 服务.

## Tests

539 passed, 0 failed. Three tests were adapted without weakening any assertion:

- **CommandPaletteTests** matches commands by their localized name, since the menu bar is
  localized and the View menu is the standard SwiftUI one. Assertions use `localizedString()`
  rather than hardcoded English.
- **ExternalChangeTests** waits for the pending state again — upstream had replaced the polling
  wait with a fixed sleep that was too short.
- **SliderSnapTests** derives the expected value from the cell's knob and track geometry instead
  of the hardcoded 0.94 of an older macOS slider. Geometry must be read after layout has run,
  otherwise knob and track come back the same width and the test passes or fails for the wrong
  reason.

## Follow-up commit

a44ccbc followed the merge with two fixes found during acceptance: the type tool's options bar
header read "类型" (the brush kind picker's translation) instead of "文字", and the slider
geometry wait above. The v1.4.7-cn tag points at a44ccbc, the final state of the cycle.
