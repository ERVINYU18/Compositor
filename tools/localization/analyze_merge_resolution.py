#!/usr/bin/env python3
"""
复核「合并进行中」时暂存区冲突标记与工作区最终选择的对照表。

背景：Compositor-CN 仓库在一次「官方 v1.4.7 合并」中途停止：
  - 暂存区(索引)里 26 个文件仍含 `<<<<<<< HEAD ... ======= ... >>>>>>> compositor-upstream-snapshot` 冲突标记
  - 工作区里这些标记已被清理，但清理结果没有重新 git add

本脚本逐处冲突列出：中文侧(ours) / 上游侧(theirs) 的内容，
并判断工作区最终保留了哪一侧（或两侧都留 / 都未采用 / 被改写）。

用法：在仓库根目录执行
    python3 analyze_merge_resolution.py
"""
import re
import subprocess
import sys

MARK_OURS = "<<<<<<< HEAD"
MARK_SEP = "======="
MARK_THEIRS = ">>>>>>>"

BLOCK_RE = re.compile(
    r"^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n",
    re.DOTALL | re.MULTILINE,
)


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def norm(text):
    """按行去首尾空白后拼接，用于判断某一段内容是否出现在最终文件里。"""
    return "\n".join(line.strip() for line in text.strip().splitlines())


def preview(text, limit=100):
    for line in text.strip().splitlines():
        s = line.strip()
        if s and not s.startswith("//") and not s.startswith("///"):
            return s[:limit]
    return "(空)"


def main():
    files = sh("git", "grep", "-l", "-e", "^<<<<<<< HEAD", "--cached", "--", ".")
    files = [f for f in files.splitlines() if f.strip()]
    if not files:
        print("暂存区没有发现冲突标记。")
        return 0

    total_hunks = 0
    tally = {"OURS": 0, "THEIRS": 0, "BOTH": 0, "REWRITTEN": 0}
    rows = []

    for path in files:
        try:
            index_text = sh("git", "show", f":{path}")
        except subprocess.CalledProcessError:
            print(f"!! 无法读取索引中的 {path}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                work_text = fh.read()
        except FileNotFoundError:
            print(f"!! 工作区缺少 {path}")
            continue

        work_norm = norm(work_text)
        hunks = BLOCK_RE.findall(index_text)
        per_file = []

        for idx, (ours, theirs) in enumerate(hunks, 1):
            total_hunks += 1
            o_in = bool(norm(ours)) and norm(ours) in work_norm
            t_in = bool(norm(theirs)) and norm(theirs) in work_norm
            if o_in and t_in:
                kind = "BOTH"
            elif o_in:
                kind = "OURS"
            elif t_in:
                kind = "THEIRS"
            else:
                kind = "REWRITTEN"
            tally[kind] += 1
            per_file.append((idx, kind, preview(ours), preview(theirs)))

        if per_file:
            rows.append((path, per_file))

    print(f"暂存区含冲突标记的文件: {len(files)} 个；冲突处: {total_hunks} 处\n")
    for path, per_file in rows:
        print(f"── {path}  （{len(per_file)} 处）")
        for idx, kind, p_ours, p_theirs in per_file:
            print(f"   [{idx}] {kind}")
            print(f"        中文侧 : {p_ours}")
            print(f"        上游侧 : {p_theirs}")
        print()

    print("=== 汇总 ===")
    print(f"  取中文侧 (OURS)      : {tally['OURS']}")
    print(f"  取上游侧 (THEIRS)    : {tally['THEIRS']}")
    print(f"  两侧都保留 (BOTH)    : {tally['BOTH']}")
    print(f"  两侧都未直接采用     : {tally['REWRITTEN']}")
    print(f"  合计                 : {total_hunks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
