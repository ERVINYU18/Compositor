# v1.7.1 conflict resolution

Round: 1.7.0 → 1.7.1, merged and installed by **Compositor-CN Updater
V2.4.1** on 2026-11-25. No handoff and **no conflict**: upstream only bumped
the version lines in `project.pbxproj`, which merge cleanly on top of the CN
patch.

## 1 Official source

- Upstream tag `v1.7.1` = `989e3d1a2a9f421f6389e8e323993ce7f7e30c88`
  (published 2026-11-24T05:19Z; release note 2026-11-24T05:31Z).
- Synthetic snapshot commit **`ad4c07d`**, parent = the v1.7.0 snapshot
  `884e53d`.
- **Content verified**: snapshot tree `f5c3158078950a828ae4db7717bdc9b57939a527`
  equals the tree of upstream commit `989e3d1a` (GitHub API). No drift.
- Tag sequence: `git ls-remote --tags upstream` lists `v1.6.15 → v1.7.0 →
  v1.7.1` with no tag in between, so nothing was skipped.
- Merge commit **`95a454e`** (parents `e9967a6` = CN branch, `ad4c07d` =
  snapshot), standard updater message.
- Version/build after the merge: **1.7.1 / 76**; Bundle ID unchanged
  (`com.wonderassembly.compositor.cn`).
- Old app archived as `pre-1.7.1-install-20261125-103957`.

## 2 What upstream 1.7.0 → 1.7.1 brings

3 upstream commits, 4 files, +63 / −22. Upstream release note (2026-11-24):

> Fixed a bug with the gradient tool's preview on layer masks

- **`Compositor/Rendering/EditorCanvas.swift`** (+3) — when the GPU canvas
  assembles a preview for a gradient that is being dragged, and the gradient's
  raster is the stroke it is drawing, it now calls `edit.applyFill()` before
  placing the mask preview. Unfilled, the mask's tiles showed nothing until
  Return committed the gradient. The Core Graphics path already filled its
  tiles as it drew.
- **`CompositorTests/GPUCanvasTests.swift`** (+41) — new
  `showsAGradientOnAMaskAsItsDragged(placedApart:)`, parameterised over
  `[false, true]`: drags a gradient on a layer's mask, checks that more than a
  20th of the canvas changes while dragging, and compares the GPU canvas with
  the Core Graphics one (mean < 1.5, over-12-levels < 1 %). `placedApart`
  moves the mask's placement off the layer, the case that used to need Return.
- **`Compositor.xcodeproj/project.pbxproj`** — version 1.7.0/75 → 1.7.1/76
  only; upstream did not touch the signing lines this round.
- **`appcast.xml`** — upstream's own feed (it publishes the 1.7.0 item in this
  range); ours is unused, the file follows upstream.

Declared `@Test` count goes 844 → **845** (one new declaration; the two
arguments run inside the same test node, so the executed count is also 845).

## 3 Conflicts

**None.** `git diff e9967a6 HEAD -- Compositor.xcodeproj/project.pbxproj`
contains only the version bump (75 → 76, 1.7.0 → 1.7.1); the CN signing block
was not on the lines upstream changed, so the merge applied cleanly and the
updater ran its gates without a handoff.

Hand check — `git diff ad4c07d HEAD -- project.pbxproj` still contains only the
CN deltas:

| Key | Upstream | CN (kept) |
|---|---|---|
| `PRODUCT_BUNDLE_IDENTIFIER` | `com.wonderassembly.compositor` | `com.wonderassembly.compositor.cn` |
| `CODE_SIGN_IDENTITY` | (unset) | `"-"` |
| `CODE_SIGN_STYLE` | Automatic | Manual |
| `DEVELOPMENT_TEAM` | `3E4X3B9Z9T` | `""` |
| `ENABLE_HARDENED_RUNTIME` | YES | NO |

Test/UI-test targets keep upstream's team and Automatic signing, as before.
`git diff --stat e9967a6 HEAD` contains only the 4 upstream files —
`Localizable.xcstrings` untouched.

## 4 Localization

- Catalog: **1580 keys**, all with zh-Hans — unchanged; the change is
  behavioural (preview fill timing), no new literal.
- `audit_strings.py`: 0 UI literals missing from the catalog; baseline entries
  only (`Text(verbatim: "T")`, empty-string key).
- `audit_keys.py`: 0 `LocalizedStringKey` gaps, 0 ternary gaps.
- Updater gates: `DynamicEnglish.txt`, `MissingTranslations.txt`,
  `patch-drift.txt` all empty; `codesign-strict.log` empty.

## 5 Build, test, install

- Updater Release build: `** BUILD SUCCEEDED **`; product 1.7.1/76,
  `Contents/MacOS/` has only `Compositor` (no debug dylib).
- `codesign -v --deep --strict`: passed on the product and on
  `/Applications/Compositor-CN.app` (re-checked in this session).
- Install: old app archived, new app installed, launch smoke passed.
- Full suite (this session, `caffeinate`-wrapped):
  - First run `build-logs/1.7.1-tests.xcresult`: **841 / 845 passed, 4 failed**
    — all four are `LayerRowDragTests` (`draggedUpOverTheBlendAndOpacity…`,
    `leavingThePanelHandsOverToAnOrdinaryDrag`,
    `anOptionDragFromLowOnTheRowStillDuplicates`,
    `aboveTheControlsItBecomesAnOrdinaryDrag`), each taking 151 s under full
    load. Same known timing flake as 1.6.14.
  - That suite alone: **9 / 9 passed** in 1–4 s each
    (`build-logs/1.7.1-layerrowdrag.log`), so the code is fine and the full-run
    failures are load-induced.
  - Second full run `build-logs/1.7.1-tests-run2.xcresult`: **845 / 845 passed,
    0 failed**, `totalTestCount = 845`; `tools/ci-test-count.py --declared`
    reports executed == declared == 845.
  - Result bundles are cleaned after the round; the summary is kept in the
    workspace at `01-merge-scene-evidence/v1.7.1-test-summary-20261125.txt`.

## 6 Manual acceptance (for the user)

1. About Compositor → 1.7.1 (76), Chinese UI, no “Check for Updates…” menu.
2. Select a layer's mask, take the gradient tool, drag a linear or radial
   gradient → the gradient appears on the mask **as you drag**, before Return.
3. Repeat with the mask **placed apart** from its layer (mask offset in the
   Layers panel) → same live preview; Return still commits as before.
4. Camera RAW / PSD-PSB import and export still behave as before.

## 7 Outcome

- Merged, built, installed, full suite green (845 / 845).
- Tag `v1.7.1-cn` → the round-closing documentation commit, archives on
  desktop and iCloud (both `shasum -c` green), branch and tag pushed.
- CI: to be recorded after the push.
