# v1.7.0 conflict resolution

Round: 1.6.15 → 1.7.0, merged and installed by **Compositor-CN Updater
V2.4.1** on 2026-11-22. No handoff; the only conflict was the usual
`project.pbxproj` version/signing block, resolved by the CN white-list patch.

## 1 Official source

- Upstream tag `v1.7.0` = `8391036b907862af3be38fdfb3dc234ddfcf8885`
  (published 2026-11-21T22:31Z).
- Synthetic snapshot commit **`884e53d`**, parent = the v1.6.15 snapshot
  `f301dd0`.
- **Content verified**: snapshot tree `5b79608e0de5b3af353326c93ef8deab795694ea`
  equals the tree of upstream commit `8391036b` (GitHub API). No drift.
- Tag sequence: `compositor-cn.snapshot-tag` went from `v1.6.15` straight to
  `v1.7.0`; `git ls-remote --tags upstream` shows no intermediate 1.6.x tag
  between them, so nothing was skipped. (Upstream jumped the minor version
  number for a one-fix release.)
- Merge commit **`ba67701`** (parents `f421cc9` = CN branch, `884e53d` =
  snapshot), standard updater message.
- Version/build after the merge: **1.7.0 / 75**; Bundle ID unchanged
  (`com.wonderassembly.compositor.cn`).
- Old app archived as `pre-1.7.0-install-20261122-203052`.

## 2 What upstream 1.6.15 → 1.7.0 brings

3 files, +26 / −19. Upstream release note (2026-11-21):

> Up and Down arrows now step the numbers in adjustment and filter panels.

- **`Compositor/UI/FilterSheet.swift`** (+4) — the numeric field in adjustment
  and filter panels gains `.arrowSteps(1 / step, …)`: Up/Down move it by its
  last displayed digit, clamped to the control's range and rounded to the
  panel's step, matching Color Balance's fields.
- **`Compositor.xcodeproj/project.pbxproj`** — version 1.6.15/74 → 1.7.0/75
  (upstream also rewrote the signing block on the same lines; see §3).
- **`appcast.xml`** — upstream's own appcast; ours is unused (Sparkle stays
  disabled), the file follows upstream.

No new source strings, no new tests: `@Test` declarations stay **844**, `CompositorTests` and the UI tests are untouched.

## 3 Conflicts

**One**, in `Compositor.xcodeproj/project.pbxproj`: upstream ships
`CODE_SIGN_STYLE = Automatic`, `DEVELOPMENT_TEAM = 3E4X3B9Z9T`,
`ENABLE_HARDENED_RUNTIME = YES` and its own bundle id on the lines the CN patch
rewrites. The updater applied `CN_PATCH_OK`, re-ran the localization and
key-carrier gates, then built.

Hand check — `git diff 884e53d HEAD -- project.pbxproj` is 8+/6− and contains
only the CN deltas:

| Key | Upstream | CN (kept) |
|---|---|---|
| `PRODUCT_BUNDLE_IDENTIFIER` | `com.wonderassembly.compositor` | `com.wonderassembly.compositor.cn` |
| `CODE_SIGN_IDENTITY` | (unset) | `"-"` |
| `CODE_SIGN_STYLE` | Automatic | Manual |
| `DEVELOPMENT_TEAM` | `3E4X3B9Z9T` | `""` |
| `ENABLE_HARDENED_RUNTIME` | YES | NO |

Test/UI-test targets keep upstream's team and Automatic signing, as before.
`git diff --stat f421cc9 HEAD` contains only the 3 upstream files —
`Localizable.xcstrings` untouched.

## 4 Localization

- Catalog: **1580 keys**, all with zh-Hans — unchanged; the only UI change is
  behavioural (arrow keys), no new literal.
- `audit_strings.py`: 0 UI literals missing from the catalog; baseline entries
  only (`Text(verbatim: "T")`, empty-string key).
- `audit_keys.py`: 0 `LocalizedStringKey` gaps, 0 ternary gaps.
- Updater gates: `DynamicEnglish.txt`, `MissingTranslations.txt`,
  `patch-drift.txt` all empty; `codesign-strict.log` empty.

## 5 Build, test, install

- Updater Release build: `** BUILD SUCCEEDED **`; product 1.7.0/75,
  `Contents/MacOS/` has only `Compositor` (no debug dylib).
- `codesign -v --deep --strict`: passed on the product and on
  `/Applications/Compositor-CN.app`.
- Install: old app archived, new app installed, launch smoke passed.
- Full suite (this session, `caffeinate`-wrapped):
  **844 / 844 passed, 0 failed**, `totalTestCount = 844`;
  `tools/ci-test-count.py --declared` reports executed == declared == 844.
  Result bundle `build-logs/1.7.0-tests.xcresult` (cleaned after the round;
  the summary is kept in the workspace at
  `01-merge-scene-evidence/v1.7.0-test-summary-20261122.txt`).

## 6 Manual acceptance (for the user)

1. About Compositor → 1.7.0 (75), Chinese UI, no “Check for Updates…” menu.
2. Adjustment / filter panel numeric fields: click a field, press Up/Down →
   the value steps by its last digit, stays inside the slider's range, and
   lands on the panel's step (e.g. 0.5 steps for a 0.5-step control).
3. Color Balance fields still behave the same (this change mirrors them).
4. Camera RAW / PSD-PSB import and export still behave as before.

## 7 Outcome

- Merged, built, installed, full suite green.
- Tag `v1.7.0-cn` → the round-closing documentation commit, archives on
  desktop and iCloud (both `shasum -c` green), branch and tag pushed.
- CI both green on the first attempt (no flake this round): branch run
  `45023335353` = success, tag run `45023339494` = success.
- Manual acceptance: pending the user's check.
