# v1.6.15 conflict resolution

Round: 1.6.14 → 1.6.15, merged and installed by **Compositor-CN Updater
V2.4.1** on 2026-11-21. One conflict, auto-resolved by the white-list patch;
no handoff branch, no manual merge.

## 1 Official source

- Upstream tag `v1.6.15` = `3990a258874bad3548b56bb32afc62cca102fa70`
  (published 2026-11-21T05:29Z).
- Synthetic snapshot commit **`f301dd0`**, parent = the v1.6.14 snapshot
  `9b17e17`.
- **Snapshot content verified**: `git rev-parse f301dd0^{tree}` =
  `0dd108d9cb72fb4447643805be9100016d0240c9`, exactly the tree of upstream
  commit `3990a258` (GitHub API). No drift, no skipped version: the previous
  snapshot tag was `v1.6.14` and the next official tag is `v1.6.15`.
- Merge commit **`dd16bfd`** (parents `7c080a3` = CN branch, `f301dd0` =
  snapshot). The updater's own commit message is the standard
  "Update Chinese build to Compositor 1.6.15".
- Version/build after the merge: **1.6.15 / 74**; Bundle ID unchanged
  (`com.wonderassembly.compositor.cn`).
- `compositor-cn.snapshot-tag` = `v1.6.15`; security backup branch
  `backup-cn-v2-20261121-162643`; old app archived as
  `pre-1.6.15-install-20261121-162857`.

## 2 What upstream 1.6.14 → 1.6.15 brings

12 files, +264 / −47. Upstream release notes (2026-11-21):

- Clipping masks now hide with their layer, show again from any eye in the
  stack, and stay together when duplicated
- Fixed an occasional bug when duplicating layers by Option-dragging
- Return now finishes typing a transform value or text size
- F toggles fullscreen even with the Layers panel selected

Code detail behind those lines:

- **`Compositor/Document/LayerGroups.swift`** — effective visibility of a
  clipping stack: a layer clipped to a hidden base does not show even with
  its own eye on. `relinkCopiedClipping` re-points copies at each other's
  copies when a clipped stack is duplicated, and a copied base stops being a
  base, so the copies don't join whatever group they landed in.
- **`Compositor/Document/EditorSession.swift`** — `hiddenClippingStack(of:)`:
  clicking the eye of a layer whose base is hidden turns the whole stack back
  on (base plus every layer clipped to it), recorded as one `Show Layers`
  edit. Used by both the click path and the visibility swipe.
- **`Compositor/UI/NativeLayerList.swift`** — `trackRowPress(_:click:)`:
  a press that drags is still an Option-drag copy, only a click clips; and
  `table.allowsTypeSelect = false`, so letters stay tool/menu keys even with
  the panel focused (the "F toggles fullscreen" fix).
- **`Compositor/Document/LiveLayerMask.swift`**, `SelectionClipboard.swift` —
  supporting changes for the above.
- **`Compositor/UI/TransformInspector.swift`** — fields gain a `returned`
  callback; Return applies the value and hands the keyboard back to the canvas.
- **`Compositor/UI/TypeControls.swift`** — Return in the text-size field
  applies and releases focus.
- **`appcast.xml`** — upstream's own appcast; ours is not used (Sparkle stays
  disabled), the file simply follows upstream.
- **`scripts/ci-tests.sh`** — `LayerRowDragTests` moved into the
  `WINDOW_SUITES` batch, because it posts synthetic mouse events and
  neighbouring suites could steal a drag's event. This is the same suite that
  flaked under full parallel load in 1.6.14.
- Tests: `LayerRowDragTests` +73 lines, `LiveMaskTests` +46 lines —
  **5 new `@Test`**, 839 → **844**.

## 3 Conflicts

**One**, in `Compositor.xcodeproj/project.pbxproj`, and it was a real
content conflict: upstream ships its own build numbers and signing settings
on the same lines the CN patch rewrites. The updater applied the white-list
`CN_PATCH_OK` resolution (log line "已自动处理已知冲突"), then re-ran the
localization and key-carrier gates before building.

Resolution inspected by hand after the merge — `git diff f301dd0 HEAD --
project.pbxproj` (8+/6−) contains exactly the CN deltas and nothing else:

| Key | Upstream | CN (kept) |
|---|---|---|
| `PRODUCT_BUNDLE_IDENTIFIER` | `com.wonderassembly.compositor` | `com.wonderassembly.compositor.cn` |
| `CODE_SIGN_IDENTITY` | (unset) | `"-"` |
| `CODE_SIGN_STYLE` | `Automatic` | `Manual` |
| `DEVELOPMENT_TEAM` | `3E4X3B9Z9T` | `""` |
| `ENABLE_HARDENED_RUNTIME` | `YES` | `NO` |
| `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` | 1.6.15 / 74 | 1.6.15 / 74 (same) |

The test/UI-test targets keep upstream's `3E4X3B9Z9T` / Automatic, as before —
only the app target is ad-hoc signed. Nothing else drifted: `git diff --stat
7c080a3 HEAD` is the 12 upstream files only, `Localizable.xcstrings` untouched.

## 4 Localization

- Catalog: **1580 keys, unchanged** from 1.6.14. Upstream introduced no new
  user-visible literal this round.
- `audit_strings.py`: 0 UI literals missing from the catalog; only the two
  known baseline entries (`Text(verbatim: "T")`, the empty-string key).
- `audit_keys.py`: 0 `LocalizedStringKey` gaps, 0 ternary gaps.
- New history-action name **`Show Layers`** already exists in the catalog
  (“显示图层”) and goes through `localizedHistoryAction()` in the Undo/Redo
  menu titles, so it renders in Chinese.
- Display-layer literals around the change are symbols/identifiers (`W`, `H`,
  `°`) or keys that already exist (`Scale` → 缩放, `Apply` → 应用); no new
  English reaches the UI.
- Updater gates: `DynamicEnglish.txt`, `MissingTranslations.txt`,
  `patch-drift.txt` all empty; `audit-keys.log` reports 0 gaps.

## 5 Build, test, install

- Build (updater, Release, derived data in `~/Library/Caches/Compositor-CN-Build`):
  `** BUILD SUCCEEDED **`, product 1.6.15/74, no `*.debug.dylib` /
  `__preview.dylib` in `Contents/MacOS/` — only `Compositor`.
- `codesign -v --deep --strict`: passed on the product and on
  `/Applications/Compositor-CN.app` (`codesign-strict.log` empty).
- Install: old app archived to `pre-1.6.15-install-20261121-162857`, new app
  installed, launch smoke passed (updater's own check).
- Full test suite (this session, not the updater — it only builds):
  **844 / 844 passed, 0 failed**, `totalTestCount = 844`;
  `tools/ci-test-count.py --declared` reports executed == declared == 844.
  Result bundle `build-logs/1.6.15-tests-run2.xcresult`.
  - First attempt was cut off when the Mac went offline mid-run (it had
    reached 970 case lines across the unit and UI bundles with 0 failures, no
    summary); the run was repeated from scratch under `caffeinate`.
- Localization counts and audits listed in §4 were taken on the merged tree.

## 6 Manual acceptance (for the user)

1. About Compositor → 1.6.15 (74), Chinese UI, no “Check for Updates…” menu.
2. Layers panel: hide the base of a clipping mask → the clipped layers stop
   showing; click the eye of any of them → the whole stack comes back, one
   undo step named 显示图层.
3. Duplicate a clipping stack with Option-drag → the copies stay clipped to
   each other, not to the old base; no stray clipping when dragging a copy
   from low on its row.
4. Transform panel: type a value, press Return → the value applies and the
   canvas takes the keyboard back (tool keys work again). Same for the text
   size field in the type tool.
5. With the Layers panel focused, press F → toggles fullscreen.
6. Camera RAW / PSD-PSB import and export still behave as before.

## 7 Outcome

- Merged, built and installed: 1.6.15 / 74, strict signature check passed.
- Full test suite: **844 / 844**, 0 failures.
- Tag `v1.6.15-cn` → `86c8405`, archives on desktop and iCloud (both
  `shasum -c` green), branch and tag pushed.
- CI: branch run `44888566357` green; tag run `44888569896` needed one
  `--failed` rerun (`localization-leak` menu flake, and the new
  `LayerRowDragTests` case under load) → attempt 2 green; the follow-up docs
  run `44890961255` hit the same leak flake and also went green on rerun.
- **Manual acceptance passed on 2026-11-21** — the user reported 验收成功
  after checking the six items above (version/Chinese UI, clipping-stack
  hide and restore, Option-drag duplicate, Return focus, F fullscreen,
  Camera RAW / PSD-PSB). Round closed.
