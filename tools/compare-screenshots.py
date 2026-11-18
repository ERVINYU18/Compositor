#!/usr/bin/env python3
"""Compare the screenshots of two runs, so a UI change can be looked over.

Informational, never a gate: any legitimate upstream UI change produces a diff, and this project
merges upstream often. The output is a report naming which screenshots changed and by how much,
plus a side-by-side image for each, uploaded as an artifact for review.

Usage:
  tools/compare-screenshots.py <baseline dir> <current dir> [output dir]

Exit codes: 0 always (unless the arguments are unusable). A diff is information, not a failure.
"""
import os
import shutil
import sys


def load_pillow():
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return None, None
    return Image, ImageChops


def main(argv):
    if len(argv) < 2:
        print("usage: tools/compare-screenshots.py <baseline> <current> [out]", file=sys.stderr)
        return 2
    baseline, current = argv[0], argv[1]
    out = argv[2] if len(argv) > 2 else "screenshot-diff"

    for d in (baseline, current):
        if not os.path.isdir(d):
            print(f"missing directory: {d}", file=sys.stderr)
            return 2

    Image, ImageChops = load_pillow()
    if Image is None:
        print("Pillow is not installed; the screenshots are still uploaded unchanged.")
        report_plain(baseline, current, out)
        return 0

    os.makedirs(out, exist_ok=True)
    names = sorted({f for f in os.listdir(current) if f.endswith(".png")} |
                   {f for f in os.listdir(baseline) if f.endswith(".png")})

    rows, changed = [], 0
    for name in names:
        a, b = os.path.join(baseline, name), os.path.join(current, name)
        if not os.path.exists(a):
            rows.append((name, "new", "—"))
            changed += 1
            continue
        if not os.path.exists(b):
            rows.append((name, "removed", "—"))
            changed += 1
            continue
        try:
            ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        except Exception as e:                      # a truncated file must not stop the report
            rows.append((name, f"unreadable: {e}", "—"))
            continue
        if ia.size != ib.size:
            rows.append((name, f"resized {ia.size} → {ib.size}", "—"))
            changed += 1
            continue
        diff = ImageChops.difference(ia, ib)
        box = diff.getbbox()
        if box is None:
            rows.append((name, "same", "0.00%"))
            continue

        # The share of pixels that changed at all, not the summed channel delta: "how much of the
        # screen moved" is the useful number when deciding whether to look at it.
        total = ia.size[0] * ia.size[1]
        histogram = diff.convert("L").histogram()
        moved = total - histogram[0]           # every pixel whose lightness is above zero
        percent = moved / total * 100
        rows.append((name, f"changed, region {box}", f"{percent:.2f}%"))
        changed += 1

        # A side-by-side, and a heat map of where it moved, for each changed screen.
        side = Image.new("RGB", (ia.size[0] * 2 + 20, ia.size[1]), (30, 30, 30))
        side.paste(ia, (0, 0))
        side.paste(ib, (ia.size[0] + 20, 0))
        side.save(os.path.join(out, f"{name[:-4]}-side-by-side.png"))
        diff.save(os.path.join(out, f"{name[:-4]}-diff.png"))

    print("Screenshot comparison")
    print("=" * 72)
    print(f"{'screen':32} {'what':32} {'moved':>8}")
    for name, what, percent in rows:
        print(f"{name:32} {what:32} {percent:>8}")
    print()
    print(f"{changed} of {len(names)} screen(s) changed.")

    lines = ["## Screenshots", "", "| screen | what | moved |", "| --- | --- | --- |"]
    lines += [f"| {n} | {w} | {p} |" for n, w, p in rows]
    lines += ["", f"{changed} of {len(names)} screen(s) changed — informational, not a failure.", ""]
    with open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return 0


def report_plain(baseline, current, out):
    """Without Pillow: say which files appeared, vanished, or changed size, and write a report.

    The report file matters even in this mode: the CI step uploads `out` as an artifact, and an
    empty directory fails that with "No files were found". Sizes are weak evidence but they still
    say "something moved", which is what a reviewer needs to know.
    """
    names = sorted({f for f in os.listdir(current) if f.endswith(".png")} |
                   {f for f in os.listdir(baseline) if f.endswith(".png")})
    os.makedirs(out, exist_ok=True)
    rows = []
    print("Screenshot comparison (no image library; sizes only)")
    print("=" * 72)
    for name in names:
        a, b = os.path.join(baseline, name), os.path.join(current, name)
        if not os.path.exists(a):
            row = (name, "new")
        elif not os.path.exists(b):
            row = (name, "removed")
        else:
            sa, sb = os.path.getsize(a), os.path.getsize(b)
            row = (name, "same bytes" if sa == sb else f"{sa} → {sb} bytes")
        rows.append(row)
        print(f"{row[0]:32} {row[1]}")

    lines = ["## Screenshots", "",
             "Pillow was unavailable, so this compares file sizes, not pixels.", "",
             "| screen | what |", "| --- | --- |"]
    lines += [f"| {n} | {w} |" for n, w in rows]
    lines += ["", f"{len(rows)} screen(s) compared — informational, not a failure.", ""]

    with open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
