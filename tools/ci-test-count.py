#!/usr/bin/env python3
"""Sum the test counts of the .xcresult bundles a CI run produced, and cross-check them.

CI runs the suites in several xcodebuild invocations (first / rest / windows / filters), so
there is no single result bundle with the whole number. This sums the TOP-LEVEL counts of
each bundle — never the per-device numbers, which double-count (a 838-test run reports
passedTests=962 at the device level, because a macOS run counts differently there).

The sums go to $GITHUB_STEP_SUMMARY when set (so the number is visible without downloading
anything) and to a JSON artifact. `--declared` cross-checks the total against the number of
`@Test` declarations in CompositorTests/, and a mismatch is reported as a failure: the
declaration count and the executed count drifting apart is how a silently-skipped suite
gets noticed.

The workflow runs the filter suites only when something they cover changed, so a scoped run
executes fewer tests than the sources declare. `--exclude-suites` names the suites that were
not run — their files are left out of the declaration count, so the check compares like with
like instead of failing on a correct scoped run.

Usage:
  tools/ci-test-count.py first.xcresult rest.xcresult [more.xcresult ...]
  tools/ci-test-count.py --declared first.xcresult rest.xcresult
  tools/ci-test-count.py --declared --exclude-suites "FilterTests LevelsTests" rest.xcresult
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO / "CompositorTests"
OUT = REPO / "tools/localization/test-count-result.json"


def summary(bundle):
    """Top-level summary of one result bundle, or None when it holds no test results."""
    try:
        out = subprocess.run(
            ["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(bundle)],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"  ! {bundle}: {e}")
        return None
    if out.returncode != 0:
        # A skipped batch (no filter suites changed) leaves no bundle; a batch that never
        # started leaves an empty one. Neither is a failure of this script.
        print(f"  - {bundle}: no test results ({out.stderr.strip().splitlines()[:1]})")
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        print(f"  ! {bundle}: unparseable summary")
        return None


def counts(s):
    """Top-level counts as the project records them.

    xcresulttool has no `totalTestCount` on summary; the executed total is the sum of the
    four buckets. Some Xcode versions do add `totalTestCount`, which is used when present.
    """
    total = s.get("totalTestCount")
    passed = s.get("passedTests", 0)
    failed = s.get("failedTests", 0)
    skipped = s.get("skippedTests", 0)
    expected = s.get("expectedFailures", 0)
    if total is None:
        total = passed + failed + skipped + expected
    return {"total": total, "passed": passed, "failed": failed,
            "skipped": skipped, "expected_failures": expected}


# `@Test` is not always first on its line: `@MainActor @Test func …` puts the attribute
# after another one. Match the attribute anywhere, but only on annotation lines — a
# mention inside a comment or a string must not count.
DECL = re.compile(r'^\s*(?:@[\w()\s,.=:"-]+\s+)*@Test\b', re.M)


def declared_tests(exclude=()):
    """How many `@Test` declarations the executed suites hold, for the cross-check.

    `exclude` names suites this run did not execute (the filter suites, when the workflow
    scoped them out); their files are left out so the check compares like with like.
    """
    if not TESTS_DIR.is_dir():
        return None
    excluded = set(exclude)
    count = 0
    for path in TESTS_DIR.rglob("*.swift"):
        if path.stem in excluded:
            continue
        try:
            count += len(DECL.findall(path.read_text(encoding="utf-8")))
        except OSError:
            pass
    return count


def parse(argv):
    """Split the arguments into the declared flag, the excluded suites, and the bundles."""
    bundles, exclude = [], []
    check_declared = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--declared":
            check_declared = True
        elif a == "--exclude-suites":
            i += 1
            if i >= len(argv):
                print("--exclude-suites needs a suite list", file=sys.stderr)
                return None
            exclude += argv[i].split()
        elif a.startswith("--"):
            print(f"unknown option {a}", file=sys.stderr)
            return None
        else:
            bundles.append(a)
        i += 1
    return check_declared, exclude, bundles


def main(argv):
    parsed = parse(argv)
    if parsed is None:
        return 2
    check_declared, exclude, bundles = parsed
    if not bundles:
        print("usage: tools/ci-test-count.py [--declared] [--exclude-suites \"A B\"] "
              "<bundle.xcresult> ...", file=sys.stderr)
        return 2

    print("Test counts")
    print("=" * 64)
    per_bundle, totals = [], {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "expected_failures": 0}
    for b in bundles:
        s = summary(b)
        if s is None:
            per_bundle.append({"bundle": Path(b).name, "counts": None})
            continue
        c = counts(s)
        per_bundle.append({"bundle": Path(b).name, "counts": c, "result": s.get("result")})
        for k in totals:
            totals[k] += c[k]
        print(f"  {Path(b).name:28} {c['total']:5} tests  "
              f"({c['passed']} passed, {c['failed']} failed, {c['skipped']} skipped)")

    print()
    print(f"  {'total':28} {totals['total']:5} tests")
    print(f"  {'passed':28} {totals['passed']:5}")
    print(f"  {'failed':28} {totals['failed']:5}")
    print(f"  {'skipped':28} {totals['skipped']:5}")

    declared = declared_tests(exclude) if check_declared else None
    mismatch = False
    if declared is not None:
        print()
        print(f"  {'@Test declarations':28} {declared:5}")
        if exclude:
            print(f"  {'excluded suites':28} {len(exclude):5}  ({', '.join(sorted(exclude))})")
        if declared != totals["total"]:
            mismatch = True
            print(f"  FAIL: executed {totals['total']} but {declared} @Test declarations — "
                  "a suite was skipped or not compiled in.")
        else:
            print("  OK: the executed count matches the declarations.")

    ok = totals["failed"] == 0 and not mismatch

    summary_lines = [
        "## Test counts",
        "",
        "| batch | tests | passed | failed | skipped |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in per_bundle:
        c = entry["counts"]
        if c is None:
            summary_lines.append(f"| {entry['bundle']} | — | — | — | — |")
        else:
            summary_lines.append(
                f"| {entry['bundle']} | {c['total']} | {c['passed']} | {c['failed']} | {c['skipped']} |")
    summary_lines += [
        f"| **total** | **{totals['total']}** | **{totals['passed']}** | "
        f"**{totals['failed']}** | **{totals['skipped']}** |",
        "",
    ]
    if declared is not None:
        verdict = "matches the declarations" if not mismatch else "DIFFERS from the declarations"
        summary_lines.append(f"`@Test` declarations: {declared} — {verdict}")
        if exclude:
            summary_lines.append(f"Excluded (not run): {', '.join(sorted(exclude))}")
        summary_lines.append("")
    summary_lines.append(f"Result: {'PASS' if ok else 'FAIL'}")
    summary_lines.append("")

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"per_bundle": per_bundle, "totals": totals, "excluded_suites": sorted(exclude),
               "declared": declared, "mismatch": mismatch, "ok": ok},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print()
    print("PASS: every batch passed." if ok else "FAIL: see above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
