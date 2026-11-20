# v1.6.14 conflict resolution

Round: 1.6.13 → 1.6.14, merged by **Compositor-CN Updater V2.4.1** on
2026-11-20. No conflicts, no handoff — the first round the updater carried
from merge to install on its own.

## 1 Official source

- Upstream tag `v1.6.14` = `d37eb51a6cb6e78a18adbfe4cccbde974e094e35`
  (published 2026-11-19T23:51Z; `gh api repos/robbietilton/Compositor/...`).
- Synthetic snapshot commit **`9b17e17`**, parent = the v1.6.13 snapshot
  `692f498`.
- Version/build after the merge: **1.6.14 / 73**. Bundle ID remains
  `com.wonderassembly.compositor.cn`.
- Merge commit: **`bce0405`** (parents `43b3d62` = CN branch, `9b17e17` =
  snapshot). Clean merge, no markers.
- No new backup branch was created by this run; the rollback point is the
  pre-merge commit `43b3d62`, which is also on `origin`.
- Tag sequence confirmed: 1.6.13 → 1.6.14 only (no skipped releases).

## 2 What upstream 1.6.13 → 1.6.14 brings

4 files, +128 / −26. Upstream release note: "Painting on a layer mask that's
been moved or resized apart from its layer no longer shows faint lines across
the stroke while you paint".

- **`Compositor/Document/LayerMask.swift`**
  - `drawSmooth` gains `hardEdged: Bool = false`; when set it turns off
    antialiasing, so the pixels the rect's edge cuts through are replaced
    rather than blended toward black.
  - `BrushStroke`'s mask commit composes every pending patch with the old mask
    into **one** `joined` image first (union of patch rects, inset by −8 px,
    background filled from the old mask's background value), then draws it
    hard-edged. Drawing the tiles one at a time let each tile's softened edge
    leave a line across the stroke until the stroke was committed.
- **`CompositorTests/TiledLayerTests.swift`** — one new parameterised test
  (`paintingAScaledDownLayer...` variants, 2×2 argument sets, 81 lines).
- **`Compositor.xcodeproj/project.pbxproj`** — version 1.6.13/72 → 1.6.14/73.
- **`appcast.xml`** — upstream's own appcast caught up to 1.6.13. Ours is not
  used (Sparkle stays disabled), the file simply follows upstream.

`@Test` declarations: 838 → **839** (+1).

## 3 Conflicts

**None.** The updater's white-list merge applied cleanly and the key-carrier
audit passed, so it proceeded straight through build and install.
`last-conflicts.txt` still holds the v1.6.13 round's list (stale, not
regenerated — it is not evidence of conflicts this round).

Rules still checked by hand after the merge:

- Display layer untouched: the catalog file was not modified
  (`git diff --name-only 43b3d62 bce0405` shows only the four files above).
- App target Release signing intact: `CODE_SIGN_IDENTITY = "-"`,
  `CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`,
  `ENABLE_HARDENED_RUNTIME = NO`; test/UI-test targets keep upstream's
  `3E4X3B9Z9T` / Automatic as before. Nothing drifted this round.

## 4 Localization

No new user-facing strings — the only Swift change is mask rasterisation.

- Catalog unchanged at **1580 keys**.
- `audit_strings.py`: 0 UI literals missing from the catalog; 1 `Text(verbatim:)`
  literal = letter T (intentional); 1 "key lacking zh-Hans" = the baseline
  empty key (present since 1.6.13, not a gap).
- `audit_keys.py`: 0 `LocalizedStringKey` gaps, 0 ternary gaps (1580 keys).
- Updater gates: `DynamicEnglish.txt` and `MissingTranslations.txt` empty,
  `patch-drift.txt` empty, `audit-keys.log` reports "no key-carrier gaps".

## 5 Build, test, install

Executed by the updater, then verified here.

- Build: Release `BUILD SUCCEEDED` (updater log). Product **1.6.14 (73)**.
- Product `codesign -v --deep --strict`: passed. `Contents/MacOS/` holds only
  `Compositor`; no `*.debug.dylib` / `__preview.dylib`.
- Install: old app archived to
  `.Compositor-CN-Backups/pre-1.6.14-install-20261120-172108/`; installed app
  is 1.6.14/73, `codesign -v --deep --strict` passed on `/Applications`, launch
  smoke passed (updater `test-app.log` has only a benign IMK warning).
- Full test, first run: **835 / 839**, 4 failures, all
  `LayerRowDragTests`. Under the full parallel load each of those GUI drag
  tests took **144 s** and the synthesised mouse events never reordered the
  layers. Re-running the suite alone: **6 / 6 pass in ~3 s each**. The drag
  code is untouched this round, so this is the documented full-load timing
  weakness of window/event-driven tests, not a regression.
- Full test, second run: **839 passed / 0 failed**,
  `totalTestCount = 839` (`build-logs/1.6.14-tests-run2.xcresult`).
  `tools/ci-test-count.py --declared` agrees: executed 839 = declarations 839.
- `git config compositor-cn.snapshot-tag` = `v1.6.14`; snapshot branch is an
  ancestor of HEAD — the updater's four "already up to date" conditions hold
  for the next run.

## 6 Environment note

This round was built and tested inside the agent session (DoubaoWork, 完全访问
mode), not in a real terminal: nested `sandbox-exec` is only refused when the
agent's own commands are Seatbelt-wrapped. Verified 2026-11-20 — Debug build,
one suite, and the full 839 all ran here. The earlier "must be run by the user
in Terminal" constraint applies only to sandboxed sessions.

`update.command` still never runs tests — the 839 above were run separately.

## 7 Manual acceptance focus

Upstream's change is one painting fix, so acceptance is narrow:

1. Pick the Move tool, move or resize a layer so its mask is offset, then paint
   on the mask: no faint horizontal/vertical line across the stroke, and the
   stroke stays a single continuous tone after mouse-up.
2. Paint the same area in several short strokes: no seams between strokes.
3. Mask edges stay crisp (no darkened fringe) where the stroke meets the mask's
   existing values.
