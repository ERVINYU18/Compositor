# v1.6.7 conflict resolution

Round: 1.6.6 → 1.6.7. This round was **merged by the updater**, not by hand —
`Compositor-CN Updater V2.2.1 (221)` fetched the tag, built the snapshot,
merged, built, and installed on 2026-11-16. The follow-up fixes in
`29bc654` were applied by hand the same day.

## 1 Where the official source came from

- Upstream tag `v1.6.7` = `1fba773fd5db5b32ff6c780b62f7456ebf777597`
  (`git ls-remote --tags upstream` through Clash on 127.0.0.1:7897).
- The updater's synthetic snapshot commit **`5060925`** ("Official snapshot
  v1.6.7"). **Not** the real upstream tag commit — the ancestry chain is
  built from tarballs, as in every earlier round.
- Merge commit **`683b1a1`** ("Update Chinese build to Compositor 1.6.7"),
  authored by `Compositor-CN Updater <local@compositor-cn>`, parents
  `25822f9` (the v1.6.6 release commit) and `5060925`.
- Version/build after the merge: **1.6.7 / 66**. Bundle ID remains
  `com.wonderassembly.compositor.cn`.
- `compositor-cn.snapshot-tag` was updated to `v1.6.7`, and the snapshot
  branch `compositor-upstream-snapshot` is an ancestor of HEAD. ✅

### Version gaps

None this round: 1.6.6 → 1.6.7 is contiguous. The 1.6.5 gap was already
absorbed in the v1.6.6 round.

Upstream `main` is one commit ahead of the tag (`08975ba`, "Publish update
feed for Compositor 1.6.7") — an appcast-only commit, no source change.

## 2 What upstream changed

9 files, `+130 / -50` in the snapshot.

| Area | Change |
| --- | --- |
| Pencil / anti-alias | "Anti-alias off paints and erases hard pixel edges, like a pencil". A new `Anti-alias` toggle in the brush bar; `Hardness` is disabled when anti-aliasing is off. |
| Brush / colour swatch | The Brush and Spot Healing bars drop the foreground colour swatch, because the tool rail already has it. |
| Scroll zoom | Option- and Command-scroll zoom in as the wheel turns away and out as it turns toward you, whichever way natural scrolling is set (#336). |

New tests: `PencilTests` (2) and `ScrollZoomTests` (1).

## 3 What the merge broke, and the fix

The merge carried the upstream `project.pbxproj` over the CN Release fixes —
exactly the failure mode AGENTS.md warns about. Two problems, both fixed in
`29bc654`:

### 3.1 Signing configuration (severe)

| Setting | After `683b1a1` | Restored to |
| --- | --- | --- |
| App/Release `CODE_SIGN_IDENTITY` | *(absent)* | `"-"` |
| App/Release `CODE_SIGN_STYLE` | `Automatic` | `Manual` |
| App/Release `DEVELOPMENT_TEAM` | `3E4X3B9Z9T` | `""` |
| App/Release `ENABLE_HARDENED_RUNTIME` | `YES` | `NO` |
| App/Debug `ENABLE_HARDENED_RUNTIME` | `YES` | `NO` |

App/Debug's other three settings were already correct and were left alone.

The restored values are the ones that built and installed cleanly at v1.6.6
(`ed7a6dc`); the same restoration was last done by `299cbf2` after the
v1.4.5 merge.

The `CompositorTests` and `CompositorUITests` targets keep
`DEVELOPMENT_TEAM = 3E4X3B9Z9T` — that is the established baseline, and
upstream now sets it too.

Why it matters: with `Automatic` style and a team ID this machine has no
certificate for, a Release build cannot be signed; and with hardened runtime
on, the embedded Sparkle framework has no Team ID, so the app aborts at
launch. The installed 1.6.7 was unaffected in practice — the updater builds
Debug, and `codesign -dv` on the installed bundle shows `flags=0x2(adhoc)`
with no hardened-runtime flag — but the next Release build would have
failed.

### 3.2 Two missing zh-Hans keys

| Key | Where | Translation |
| --- | --- | --- |
| `Smooth edges; turn off for hard pixel edges, like a pencil` | `Compositor/UI/BrushControls.swift:120` (the new Anti-alias toggle's help text) | 平滑边缘；关闭后保留清晰的像素边缘，就像铅笔一样 |
| `Text` | `Compositor/UI/LayerSearchControls.swift:14` (the text layer type in the filter toggle) | 文本 |

The first was reported by `tools/localization/audit_strings.py`. The second
**was not** — `audit_strings.py` cannot see a key carried by a
`LocalizedStringKey` switch, which is one of its documented blind spots.
It had been missing since at least v1.6.4 (checked `ed7a6dc`, `25822f9`,
`26f14c8` — none has the key). It was found by a separate sweep over every
`var x: LocalizedStringKey` and `-> LocalizedStringKey` body in the tree.

Deliberately **not** translated: the layer defaults `"Folder 1"`,
`"Layer Mask"` and `TypeTool`'s `"Text"` content string are stored data
(names in `.comp` files and in the layers panel), not UI labels.

## 4 Localization verification

- `tools/localization/audit_strings.py`: **1566** catalog keys, **0** UI
  literals outside the catalog, **0** `Text(verbatim:)` literals. The one
  key "lacking zh-Hans" is the baseline empty-string key, not a gap.
- `LocalizedStringKey` sweep across the whole tree: **0** missing keys.
- Ternary-expression sweep (the other documented blind spot): the literals
  in `BrushControls`, `ColorPaletteControls`, `ColorRangeSheet`,
  `FilterSheet`, `LayersPanel`, `LevelsSheet` and `NavigationToolHeader`
  are all in the catalog.
- The 40 UI files where the merge result differs from upstream by 475 lines
  are our **retained** Chinese localisations — not pollution to be reverted.
  Upstream v1.6.7 moved several `localizedString(...)` calls back to bare
  literals (`BlendModePicker`'s `setAccessibilityLabel("Blend mode")`,
  CameraRaw's `"Edit \(...)."`, `ColorPickerSheet`'s `Text(title)`, the
  preview's `"Hide \(name) in the preview"`); the merge kept our versions.
- `Localizable.xcstrings` was edited with the same serialisation the file
  already uses (`json.dumps(..., ensure_ascii=False, indent=2)` plus a
  trailing newline); a re-serialise-and-compare check passes.

## 5 Not verified in this round

The Release build, the full test run and the launch smoke test could not be
run from the WorkBuddy session: `xcodebuild` cannot start there at all,
because nested `sandbox-exec` is refused outright
(`sandbox_apply: Operation not permitted` even for
`sandbox-exec -p '(version 1)(allow default)' /bin/echo`). See the
"环境限制" section in `.workbuddy-ai/memory/MEMORY.md` for every workaround
tried and why each one fails.

Consequences for this round:

- The **806-test baseline is stale**. v1.6.7 adds 3 `@Test` cases, so the
  real number must be re-taken with
  `xcrun xcresulttool get test-results summary --path <xcresult>` (read the
  top-level `totalTestCount`, not the device-level figure).
- The updater never runs tests at all: `update.command` only ever calls
  `xcodebuild ... build`. Every round so far has been tested by hand.
- A launch smoke test still has to be redone after the signing fix is
  applied, since the installed bundle predates it.

## 6 Release

- Merge commit `683b1a1`, fix commit **`29bc654`** (signed by Yuyi).
- **Not pushed.** `origin/adapt-compositor-1.4.1` is still at `25822f9`
  (the v1.6.6 release commit). No `v1.6.7-cn` tag exists yet.
- No `post-1.6.7-cn-*` archive and no `pre-1.6.7-install-*` rollback point.
  The backup taken before the signing fix lives at
  `.Compositor-CN-Backups/pre-1.6.7-signing-fix-20261116-122847/`.
- Installed app: **1.6.7 / 66**, launch smoke test passed on 2026-11-16
  (process alive ≥6 s).

## 7 Manual acceptance focus

1. Brush bar with a pencil: the **Anti-alias** toggle appears, turning it
   off disables **Hardness**, and strokes come out with hard pixel edges.
2. The brush bar no longer shows the foreground colour swatch — check the
   tool rail still offers it.
3. Scroll zoom: turn the wheel away and toward the user with natural
   scrolling on and off, and with Option/Command held; zoom should follow
   the wheel.
4. The text layer type in the layers filter reads **文本**, not "Text".
5. The new Anti-alias help text reads 平滑边缘；关闭后保留清晰的像素边缘，就像铅笔一样.
