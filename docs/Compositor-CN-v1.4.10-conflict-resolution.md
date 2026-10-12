# Compositor-CN 1.4.10 merge conflict decisions

Baseline: Chinese adaptation `adapt-compositor-1.4.1` at `9990a10` (tag `v1.4.9-cn`).
Official release: v1.4.10, upstream tag commit `eb1fda73e97dbaf5a56ddbf237b712721b37050a`.
Merge source: synthetic snapshot commit `1fb57a2`, whose parent is the v1.4.9 upstream snapshot `0ab3ff5`.
Compositor-CN merge commit: `5408843` (parents: `9990a10` + `1fb57a2`).

## Source provenance — important caveat

`git fetch upstream --tags` was unavailable in this environment: the sandbox proxy returned repeated 502s,
and a direct fetch from Terminal timed out after 75 seconds. The official source archive was downloaded
from GitHub's codeload endpoint and verified to contain `MARKETING_VERSION = 1.4.10`.
The archive tree was committed on a temporary worktree based on upstream v1.4.9, producing synthetic
commit `1fb57a2`. This gives Git a merge parent and preserves a comparable source tree, but it is **not**
the real upstream tag commit `eb1fda7`; the upstream history between v1.4.9 and v1.4.10 is not present
in this snapshot's ancestry. Keep this caveat in future merge records and archives; do not describe
`1fb57a2` as the upstream commit.

The Compositor-CN updater attempted the same merge first and rolled it back after the conflicts below.
The rollback was clean; the manual merge began from HEAD `9990a10` with no residual merge state.

## Conflicts and resolutions

| File | Official v1.4.10 change | Existing Chinese customization | Resolution |
|---|---|---|---|
| `Compositor.xcodeproj/project.pbxproj` (2 hunks) | Updates marketing version and official bundle identifier. | The app target uses `com.wonderassembly.compositor.cn`; Release is configured for ad-hoc signing. | Took version `1.4.10`, kept the CN bundle ID. Re-verified app Release: `CODE_SIGN_IDENTITY = "-"`, `CODE_SIGN_STYLE = Manual`, `DEVELOPMENT_TEAM = ""`, `ENABLE_HARDENED_RUNTIME = NO`. The four `3E4X3B9Z9T` values remain only in test targets, at the same locations as the 1.4.9 baseline. |
| `Compositor/IO/ImageFileDrop.swift` | Adds HEIF to accepted file formats and the unsupported-drop message. | The existing message uses `localizedString()` and already mentions WebP. | Kept localization and WebP; added HEIF to the message. |
| `Compositor/IO/ImageImporter.swift` | Adds HEIF support and updates the unsupported-format message. | Chinese wording adds Photoshop Large Document (PSB), which upstream omits; errors use localized format strings. | Kept the localized unreadable/size messages, added HEIF, retained PSB, and kept WebP. |
| `Compositor/UI/BlendModePicker.swift` | Adds `sizeThatFits` so the native blend-mode popup respects the narrow Layers panel width. | The existing wrapper was localized. | Kept the upstream layout fix; it adds no user-facing strings. |
| `Compositor/UI/RawDevelopSheet.swift` | Adds noise reduction, lens correction, highlight recovery, and associated support-dependent help. Changes the label width from 90 to 110 points. | Slider titles are English `String` variables; `Text(title)` does not look up String Catalog entries. The Chinese path uses `localizedString(title)`. | Kept the larger upstream width (110) but retained `Text(verbatim: localizedString(title))`. Added zh-Hans for the new Highlight Recovery label and all conditional help strings. English the user sees is still looked up in the catalog. |

All five files passed `xcrun swiftc -parse`. No conflict markers remain in the worktree or index.

## Other notable official changes

- Gaussian Blur gains a Preserve Transparency toggle and help description; added both zh-Hans entries.
- HEIF is declared in `Config/Info.plist`; upstream adds a folder document-handler entry. Kept these declarations.
- Upstream adds `PatchPixels.c/.h`, Spot Healing tests, a Screenshots scheme and screenshot UI tests, plus `scripts/ci-tests.sh`.
- `Config/Info.plist` contains no official Sparkle feed keys after the merge. The app's updater entry remains disabled.

## Localization audit

The String Catalog grew from 1141 to 1151 keys; all keys have zh-Hans. Static audit results contain only the
untranslated generic separators `·` and `×`.

Important audit gap discovered this round: the static audit did not report help strings inside ternary
expressions such as `.help(condition ? "available text" : "unavailable text")`. The new Raw Develop help
strings were found by reviewing the upstream diff. Continue reviewing conditional UI strings manually.

## Verification status

Debug test session: `/Users/yi/Library/Developer/Xcode/DerivedData/Compositor-davdrrubavvtxcbhvolgpttvmeho/Logs/Test/Test-Compositor-2026.10.12_10-36-49-+0800.xcresult`

- Result: Passed
- Top-level `totalTestCount` / `passedTests`: **577**
- `failedTests`: **0**; expected failures: 0; skipped: 0
- Failure summaries: 0; error summaries: 0; runtime warnings: 0
- Device-level `passedTests` reports 651 because parameterized runs are counted there; use the top-level 577 as the suite baseline.

Release build, launch smoke test, installation and manual acceptance are still pending. Append those results after they are completed.
