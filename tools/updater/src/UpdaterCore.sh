#!/bin/bash
# Shared, sourceable safety functions for updater runtime and isolated tests.

scan_dynamic_english() {
    local output="$1"

    python3 - "$REPO" "$output" <<'PY_SCAN'
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
output = Path(sys.argv[2])

patterns = [
    # rawValue 直接进入 UI
    re.compile(
        r'(?:Text|Button|Label|help|accessibilityLabel|'
        r'setAccessibilityLabel|addItem\s*\(\s*withTitle:|'
        r'selectItem\s*\(\s*withTitle:)[^\n]*\.rawValue'
    ),

    # AppKit 字符串不会自动经过 SwiftUI String Catalog
    re.compile(
        r'(?:setAccessibilityLabel|setToolTip)\s*\(\s*"[^"]*[A-Za-z]'
    ),
    re.compile(
        r'(?:addItem|selectItem)\s*\(\s*withTitle:\s*"[^"]*[A-Za-z]'
    ),
    re.compile(
        r'labelWithString:\s*"[^"]*[A-Za-z]'
    ),
    re.compile(
        r'NSMenuItem\s*\(\s*title:\s*"[^"]*[A-Za-z]'
    ),

    # 动态 title/name 直接进入 SwiftUI，而没有显式本地化
    re.compile(
        r'(?:Text|Button|Label)\s*\(\s*'
        r'[A-Za-z_][A-Za-z0-9_.]*(?:Title|Name|title|name)\s*\)'
    ),

    # 英文 literal 与动态内容直接拼接后送进 UI
    re.compile(
        r'(?:Text|Button|Label|accessibilityLabel|help|'
        r'setAccessibilityLabel)\s*\([^)\n]*'
        r'"[^"]*[A-Za-z][^"]*"\s*\+'
    ),
]

safe_markers = (
    "localizedString(",
    ".localizedName",
    "LocalizedStringKey(",
)

rows = []

for path in sorted((repo / "Compositor").rglob("*.swift")):
    rel = path.relative_to(repo).as_posix()

    try:
        lines = path.read_text().splitlines()
    except UnicodeDecodeError:
        continue

    for number, line in enumerate(lines, 1):
        stripped = line.strip()

        if not stripped or stripped.startswith("//"):
            continue

        if any(x in stripped for x in safe_markers):
            continue

        if not any(pattern.search(stripped) for pattern in patterns):
            continue

        normalized = " ".join(stripped.split())
        signature = f"{rel}|{normalized}"

        rows.append(
            (signature, rel, number, normalized)
        )

with output.open("w", encoding="utf-8") as f:
    for signature, rel, number, text in rows:
        f.write(
            f"{signature}\t{rel}:{number}: {text}\n"
        )

print(len(rows))
PY_SCAN
}

pause_exit() {
    echo
    read -r -p "按回车键关闭窗口…" _ || true
    exit "${1:-0}"
}

fail() {
    echo
    echo "❌ $1"

    if [ "${TRANSACTION_ACTIVE:-0}" -eq 1 ]; then
        rollback
    fi

    pause_exit 1
}

rollback() {
    if [ "${ROLLBACK_COMPLETE:-0}" -eq 1 ] ||
       [ "${ROLLBACK_IN_PROGRESS:-0}" -eq 1 ]; then
        return 0
    fi

    ROLLBACK_IN_PROGRESS=1
    trap - ERR

    echo
    echo "↩️ 正在恢复更新前状态…"

    killall Compositor 2>/dev/null || true

    # 恢复正式 App 安装事务
    if [ "${INSTALL_SWAPPED:-0}" -eq 1 ]; then
        echo "↩️ 正在恢复旧的正式 App…"

        if [ -d "${INSTALL_BACKUP:-}" ]; then
            if [ -e "$APP" ]; then
                sudo rm -rf "$INSTALL_NEW" >/dev/null 2>&1 || true
                sudo mv "$APP" "$INSTALL_NEW" >/dev/null 2>&1 || true
            fi

            if sudo mv "$INSTALL_BACKUP" "$APP" >/dev/null 2>&1; then
                sudo rm -rf "$INSTALL_NEW" >/dev/null 2>&1 || true
                INSTALL_SWAPPED=0
                INSTALL_OLD_MOVED=0
                echo "✅ 已恢复更新前正式 App。"
            else
                # 至少尝试把刚才的新版本放回正式路径，避免 APP 路径为空
                if [ -d "${INSTALL_NEW:-}" ] && [ ! -e "$APP" ]; then
                    sudo mv "$INSTALL_NEW" "$APP" >/dev/null 2>&1 || true
                fi

                echo "⚠️ 正式 App 自动恢复失败。"
                echo "旧版备份仍保存在：$INSTALL_BACKUP"
            fi
        fi

    elif [ "${INSTALL_OLD_MOVED:-0}" -eq 1 ]; then
        if [ -d "${INSTALL_BACKUP:-}" ] && [ ! -e "$APP" ]; then
            if sudo mv "$INSTALL_BACKUP" "$APP" >/dev/null 2>&1; then
                INSTALL_OLD_MOVED=0
                echo "✅ 已恢复更新前正式 App。"
            else
                echo "⚠️ 正式 App 自动恢复失败。"
                echo "旧版备份仍保存在：$INSTALL_BACKUP"
            fi
        fi
    fi

    if [ -n "${INSTALL_NEW:-}" ] && [ -e "$INSTALL_NEW" ]; then
        sudo rm -rf "$INSTALL_NEW" >/dev/null 2>&1 || true
    fi

    cd "$REPO" 2>/dev/null || {
        echo "⚠️ 无法进入源码仓库，自动恢复无法完成。"
        ROLLBACK_IN_PROGRESS=0
        return 1
    }

    # 防止 snapshot branch 仍被临时 worktree 占用
    if [ -n "${WORKTREE:-}" ]; then
        git worktree remove "$WORKTREE" --force >/dev/null 2>&1 || true
    fi
    git worktree prune >/dev/null 2>&1 || true

    if git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
        git merge --abort >/dev/null 2>&1 || true
    fi

    # 恢复中文版分支到更新前 HEAD
    if [ -n "${ORIGINAL_CN_HEAD:-}" ]; then
        git reset --hard "$ORIGINAL_CN_HEAD" >/dev/null 2>&1 || true
    elif [ -n "${BACKUP_BRANCH:-}" ] &&
         git show-ref --verify --quiet "refs/heads/$BACKUP_BRANCH"; then
        git reset --hard "$BACKUP_BRANCH" >/dev/null 2>&1 || true
    fi

    # 恢复更新前的官方 snapshot branch
    if [ "${ORIGINAL_SNAPSHOT_EXISTS:-0}" -eq 1 ]; then
        if [ -n "${ORIGINAL_SNAPSHOT_HEAD:-}" ]; then
            git branch -f \
                "$SNAPSHOT_BRANCH" \
                "$ORIGINAL_SNAPSHOT_HEAD" >/dev/null 2>&1 || true
        fi
    else
        git branch -D "$SNAPSHOT_BRANCH" >/dev/null 2>&1 || true
    fi

    # 恢复更新前的 snapshot-tag
    if [ "${ORIGINAL_SNAPSHOT_TAG_SET:-0}" -eq 1 ]; then
        git config \
            compositor-cn.snapshot-tag \
            "$ORIGINAL_SNAPSHOT_TAG" >/dev/null 2>&1 || true
    else
        git config --unset-all \
            compositor-cn.snapshot-tag >/dev/null 2>&1 || true
    fi

    MERGE_ACTIVE=0
    TRANSACTION_ACTIVE=0
    ROLLBACK_COMPLETE=1
    ROLLBACK_IN_PROGRESS=0

    echo "✅ 已执行源码事务回滚。"
    trap 'on_unexpected_error "$?" "$BASH_COMMAND" "$LINENO"' ERR
}

on_unexpected_error() {
    local status="${1:-1}"
    local failed_command="${2:-unknown command}"
    local failed_line="${3:-unknown line}"

    # 先关闭 ERR trap，避免 handler 和 rollback 中的错误递归进入自身。
    trap - ERR
    set +e

    echo
    echo "❌ 更新器遇到未处理异常（exit ${status}，line ${failed_line}）。"
    echo "命令：$failed_command"

    if [ "${TRANSACTION_ACTIVE:-0}" -eq 1 ]; then
        rollback || true
    fi

    echo "已执行或尝试执行安全回滚；如有异常请查看上方提示。"
    exit "$status"
}

trap 'on_unexpected_error "$?" "$BASH_COMMAND" "$LINENO"' ERR

check_missing_zh_hans() {
    local catalog="$1"
    local output="$2"

    python3 - "$catalog" "$output" <<'PY_CATALOG'
import json
import sys
from pathlib import Path

catalog = Path(sys.argv[1])
output = Path(sys.argv[2])
missing = []

if catalog.exists():
    data = json.loads(catalog.read_text())
    for key, item in data.get("strings", {}).items():
        if item.get("shouldTranslate") is False:
            continue
        zh = item.get("localizations", {}).get("zh-Hans")
        if not zh:
            missing.append(key)

output.write_text("\n".join(sorted(missing)), encoding="utf-8")
print(len(missing))
PY_CATALOG
}


install_app_transaction() {
    local source_app="$1"
    local expected_version="$2"
    local expected_build="$3"

    INSTALL_NEW="${APP}.new.$$"
    INSTALL_BACKUP="${APP}.rollback.$$"
    INSTALL_OLD_MOVED=0
    INSTALL_SWAPPED=0

    sudo rm -rf "$INSTALL_NEW" "$INSTALL_BACKUP"

    sudo ditto "$source_app" "$INSTALL_NEW" ||
        fail "复制新版本到 staging 失败。"

    local staged_version staged_build staged_bundle
    staged_version="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$INSTALL_NEW/Contents/Info.plist" 2>/dev/null || true)"
    staged_build="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$INSTALL_NEW/Contents/Info.plist" 2>/dev/null || true)"
    staged_bundle="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$INSTALL_NEW/Contents/Info.plist" 2>/dev/null || true)"

    if [ "$staged_bundle" != "com.wonderassembly.compositor.cn" ] ||
       [ "$staged_version" != "$expected_version" ] ||
       [ "$staged_build" != "$expected_build" ] ||
       [ ! -x "$INSTALL_NEW/Contents/MacOS/Compositor" ]; then
        fail "staging App 安全检查失败，旧正式版未被修改。"
    fi

    local source_hash staged_hash
    source_hash="$(shasum -a 256 "$source_app/Contents/MacOS/Compositor" | awk '{print $1}')"
    staged_hash="$(shasum -a 256 "$INSTALL_NEW/Contents/MacOS/Compositor" | awk '{print $1}')"
    [ "$source_hash" = "$staged_hash" ] ||
        fail "staging App 可执行文件校验失败。"

    if [ -e "$APP" ]; then
        sudo mv "$APP" "$INSTALL_BACKUP" ||
            fail "无法保留当前正式版，安装已停止。"
        INSTALL_OLD_MOVED=1
    fi

    sudo mv "$INSTALL_NEW" "$APP" ||
        fail "新版本切换失败。"
    INSTALL_SWAPPED=1

    local installed_version installed_build installed_bundle installed_hash
    installed_version="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Contents/Info.plist" 2>/dev/null || true)"
    installed_build="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$APP/Contents/Info.plist" 2>/dev/null || true)"
    installed_bundle="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Contents/Info.plist" 2>/dev/null || true)"
    installed_hash="$(shasum -a 256 "$APP/Contents/MacOS/Compositor" 2>/dev/null | awk '{print $1}')"

    if [ "$installed_bundle" != "com.wonderassembly.compositor.cn" ] ||
       [ "$installed_version" != "$expected_version" ] ||
       [ "$installed_build" != "$expected_build" ] ||
       [ "$installed_hash" != "$source_hash" ]; then
        fail "正式安装后的 App 校验失败。"
    fi

    # V2.4.0: verify the signature seal, not just the version and executable hash.
    # A ditto merge can leave stale files from the old bundle inside the new one;
    # the app still launches (ad-hoc signing is not enforced at launch) but the
    # seal is broken. That must fail the transaction.
    # Keep codesign's diagnostics: the v1.6.7 stale-dylib incident was found
    # through its "file added: ...debug.dylib" line. Swallowing stderr here
    # would hide exactly the evidence needed to diagnose a failed install.
    local seal_log="${STATE_DIR:-/tmp}/codesign-strict.log"
    if ! codesign -v --deep --strict "$APP" >"$seal_log" 2>&1; then
        echo "  codesign 诊断已写入：$seal_log"
        cat "$seal_log" >&2
        fail "正式安装后的签名 seal 校验失败（codesign --deep --strict）。"
    fi
}

# Localization gates are not integrity failures: the merge itself is sound, only the
# Chinese copy is unfinished. Rolling back threw that merge away and forced the whole
# thing to be redone by hand. Park it on a branch instead — the repo returns to exactly
# the state it had before the run, plus one branch holding the merged tree.
handoff_for_localization() {
    local reason="${1:-需要人工完成本地化}"
    local report="${2:-}"
    local stage="${3:-missing-keys}"
    local tag="${LATEST_TAG:-unknown}"
    local wip_branch="wip-cn-${tag#v}-needs-localization"
    local handoff_round_now
    handoff_round_now="$(handoff_round 2>/dev/null || echo 0)"

    # V2.4.1: three rounds, then a numbered menu instead of another parking.
    if [ "$handoff_round_now" -ge 3 ]; then
        trap - ERR
        handoff_failure_menu
        pause_exit 1
    fi

    trap - ERR
    set +e

    echo
    echo "⏸  ${reason}"
    echo

    cd "$REPO" 2>/dev/null || {
        echo "⚠️ 无法进入源码仓库，退回回滚流程。"
        TRANSACTION_ACTIVE=1
        fail "$reason"
    }

    # A leftover unresolved conflict would commit conflict markers; refuse instead.
    if [ -n "$(git diff --name-only --diff-filter=U 2>/dev/null)" ]; then
        echo "⚠️ 仍有未解决冲突，退回回滚流程。"
        TRANSACTION_ACTIVE=1
        fail "$reason"
    fi

    git add -A >/dev/null 2>&1

    local commit_msg
    commit_msg="$(
        printf '%s\n\n' "$reason"
        printf 'Compositor-CN Updater V%s 自动合并 %s 后停在本地化门禁。\n' "${VERSION:-?}" "$tag"
        [ -n "$report" ] && printf '清单：%s\n' "$report"
        printf '\n合并结果完整，只差中文本地化。接手后补词条即可，不必重做合并。\n'
    )"

    if ! git -c user.name='Compositor-CN Updater' \
             -c user.email='local@compositor-cn' \
             commit -q -m "$commit_msg" >/dev/null 2>&1; then
        echo "⚠️ 无法提交合并结果，退回回滚流程。"
        TRANSACTION_ACTIVE=1
        fail "$reason"
    fi

    local merged_head
    merged_head="$(git rev-parse HEAD)"

    if git show-ref --verify --quiet "refs/heads/$wip_branch"; then
        wip_branch="${wip_branch}-$(date +%H%M%S)"
    fi
    git branch "$wip_branch" "$merged_head" >/dev/null 2>&1

    # Back to the pre-run state; only the branch above survives.
    if [ -n "${ORIGINAL_CN_HEAD:-}" ]; then
        git reset --hard "$ORIGINAL_CN_HEAD" >/dev/null 2>&1
    elif [ -n "${BACKUP_BRANCH:-}" ] &&
         git show-ref --verify --quiet "refs/heads/$BACKUP_BRANCH"; then
        git reset --hard "$BACKUP_BRANCH" >/dev/null 2>&1
    fi

    if [ "${ORIGINAL_SNAPSHOT_EXISTS:-0}" -eq 1 ]; then
        if [ -n "${ORIGINAL_SNAPSHOT_HEAD:-}" ]; then
            git branch -f "$SNAPSHOT_BRANCH" "$ORIGINAL_SNAPSHOT_HEAD" >/dev/null 2>&1
        fi
    else
        git branch -D "$SNAPSHOT_BRANCH" >/dev/null 2>&1
    fi

    if [ "${ORIGINAL_SNAPSHOT_TAG_SET:-0}" -eq 1 ]; then
        git config compositor-cn.snapshot-tag "$ORIGINAL_SNAPSHOT_TAG" >/dev/null 2>&1
    else
        git config --unset-all compositor-cn.snapshot-tag >/dev/null 2>&1
    fi

    MERGE_ACTIVE=0
    TRANSACTION_ACTIVE=0
    ROLLBACK_COMPLETE=1
    ROLLBACK_IN_PROGRESS=0

    echo "✅ 合并结果已停在分支：$wip_branch"
    echo "   提交：$merged_head"
    echo "   正式版 App 未改动，源码分支已回到更新前状态。"

    # V2.4.1: persist the structured bundle for the AI-side protocol.
    SNAPSHOT_HEAD="$merged_head^2" write_handoff_bundle \
        "$stage" "$reason" "$report" "$wip_branch"

    echo
    echo "接手方式：到 WorkBuddy 说一句「继续更新」。"
    echo "AI 按交接包处理完，回到这里按回车续跑。"
    echo "（手动方式：cd $REPO && git checkout ${wip_branch}）"
    echo

    pause_exit 3
}

# ------------------------------------------------------------------
# V2.4.1 handoff protocol (stage 2)
#
# A handoff is not a failure: the merge is sound, only a semantic decision
# is outstanding. We park the merged tree on a wip branch, return the repo
# to its pre-run state, and write a structured bundle that any agent can
# pick up with one instruction ("继续更新"). The updater then resumes from
# the wip branch instead of redoing the merge.
#
# Bundle layout under STATE_DIR/handoff/:
#   manifest.json                 round/stage/heads/tag/reasons
#   dynamic-english-baseline.txt  persistent (TMP_ROOT dies on exit)
#   evidence/                     gate reports, conflict lists, upstream diff
#   INSTRUCTIONS.md               what the AI must do and how to signal done
#   DONE.json                     written by the AI on completion
# ------------------------------------------------------------------

HANDOFF_DIR="${STATE_DIR:-/tmp}/handoff"

# Write a structured handoff bundle. Called by every gate before pause_exit.
# Args: $1 stage (conflicts|dynamic-english|missing-keys|key-carriers|patch-drift)
#       $2 reason (human readable)
#       $3 evidence file (optional, may be empty)
#       $4 wip branch name
write_handoff_bundle() {
    local stage="${1:-unknown}"
    local reason="${2:-需要人工处理}"
    local evidence="${3:-}"
    local wip_branch="${4:-}"
    local round=1
    local existing="$HANDOFF_DIR/manifest.json"

    # Resume of an existing handoff? Bump the round (capped by caller).
    if [ -f "$existing" ]; then
        round="$(python3 - "$existing" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    print(int(d.get("round", 0)) + 1)
except Exception:
    print(1)
PY
)"
    fi

    mkdir -p "$HANDOFF_DIR/evidence" || return 1

    # Persist the dynamic-English baseline; without this a resume cannot diff.
    if [ -n "${DYNAMIC_BASELINE:-}" ] && [ -f "$DYNAMIC_BASELINE" ]; then
        cp "$DYNAMIC_BASELINE" "$HANDOFF_DIR/dynamic-english-baseline.txt" 2>/dev/null || true
    fi

    if [ -n "$evidence" ] && [ -f "$evidence" ]; then
        cp "$evidence" "$HANDOFF_DIR/evidence/$(basename "$evidence")" 2>/dev/null || true
    fi
    [ -f "${STATE_DIR:-/tmp}/last-conflicts.txt" ] && \
        cp "${STATE_DIR:-/tmp}/last-conflicts.txt" "$HANDOFF_DIR/evidence/last-conflicts.txt" 2>/dev/null || true
    [ -f "${STATE_DIR:-/tmp}/DynamicEnglish.txt" ] && \
        cp "${STATE_DIR:-/tmp}/DynamicEnglish.txt" "$HANDOFF_DIR/evidence/DynamicEnglish.txt" 2>/dev/null || true
    [ -f "${STATE_DIR:-/tmp}/MissingTranslations.txt" ] && \
        cp "${STATE_DIR:-/tmp}/MissingTranslations.txt" "$HANDOFF_DIR/evidence/MissingTranslations.txt" 2>/dev/null || true

    # Full upstream diff snapshot → next snapshot, for semantic review.
    if [ -n "${ORIGINAL_SNAPSHOT_HEAD:-}" ] && [ -n "${SNAPSHOT_HEAD:-}" ]; then
        ( cd "$REPO" && git diff "$ORIGINAL_SNAPSHOT_HEAD" "$SNAPSHOT_HEAD" ) \
            > "$HANDOFF_DIR/evidence/upstream-changes.diff" 2>/dev/null || true
    fi

    ( cd "$REPO" && python3 "$AUDIT_KEYS_SCRIPT" ) \
        > "$HANDOFF_DIR/evidence/audit.json" 2>/dev/null || true

    python3 - "$HANDOFF_DIR/manifest.json" \
        "$round" "$stage" "${LATEST_TAG:-unknown}" "$wip_branch" \
        "${ORIGINAL_CN_HEAD:-}" "${SNAPSHOT_HEAD:-}" \
        "${ORIGINAL_SNAPSHOT_TAG:-}" "${BACKUP_BRANCH:-}" \
        "$reason" <<'PY'
import json, sys, datetime
path, round_, stage, tag, wip, cn_head, snap_head, snap_tag, backup, reason = sys.argv[1:11]
reasons = []
try:
    prev = json.load(open(path))
    reasons = list(prev.get("reasons", []))
except Exception:
    pass
reasons.append(reason)
data = {
    "round": int(round_),
    "stage": stage,
    "latest_tag": tag,
    "wip_branch": wip,
    "original_cn_head": cn_head,
    "snapshot_branch_head": snap_head,
    "original_snapshot_tag": snap_tag,
    "backup_branch": backup,
    "reasons": reasons,
    "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
}
json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY

    cat > "$HANDOFF_DIR/INSTRUCTIONS.md" <<'MD'
# 更新器交接包 — AI 处理指令

用户会对你说「继续更新」。按下面步骤做，**不要构建、不要推送、不要装机**。

1. 读 `manifest.json`，确认 `wip_branch`、`round`、`stage`；`evidence/` 里有门禁报告和上游完整 diff。
2. `cd <仓库>` → `git checkout <wip_branch>`（分支已含合并结果与冲突标记）。
3. 按 `AGENTS.md` 取舍冲突：**显示层保留中文，行为层保留上游**。禁止"全部 ours/theirs"或整文件覆盖。
4. 补词条照 `docs/Compositor-CN-requirements.md` 的术语表；`Text(verbatim:)` 只用于 T 这类标识符；数据用名（ColorSync 名、Codable rawValue、快捷键 title）不译。
5. 自查：跑 `tools/localization/audit_strings.py` 和 `tools/localization/audit_keys.py`，再人工补扫枚举/三元/AppKit setter 三类盲区。
6. 在 wip 分支提交（清晰写每个冲突取了哪边、为什么）。起草本轮冲突记录草稿放工作区 `Compositor-CN-vX.Y.Z-conflict-resolution.md`。
7. 写 `DONE.json` 到本目录：
   ```json
   {"round": <与 manifest 一致>, "changed_files": ["..."], "decisions": ["文件: 取哪边/为什么"], "unresolved": []}
   ```
   `unresolved` 非空也要如实写，交给用户判断。
8. 告诉用户：「回更新器按回车继续」。剩下的构建、测试、装机、推送由更新器和用户完成。
MD

    echo "交接包已写入：${HANDOFF_DIR} （round $round, stage ${stage}）"
}

# Check whether a handoff is pending and its wip branch still exists.
pending_handoff() {
    [ -f "$HANDOFF_DIR/manifest.json" ] || return 1
    local wip
    wip="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("wip_branch",""))' "$HANDOFF_DIR/manifest.json" 2>/dev/null)"
    [ -n "$wip" ] || return 1
    ( cd "$REPO" && git show-ref --verify --quiet "refs/heads/$wip" ) || return 1
    return 0
}

# Round cap: 3 handoff rounds, then a numbered menu instead of another round.
handoff_round() {
    python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("round",0))' "$HANDOFF_DIR/manifest.json" 2>/dev/null || echo 0
}

# Park an unresolved merge (conflict markers included) on a wip branch.
# Unlike localization gates, the tree here still has <<<<<<< markers, so
# handoff_for_localization would refuse to commit it. That is correct for a
# finished merge but wrong here — the AI needs those markers to resolve.
handoff_for_conflicts() {
    local conflicts_file="${1:-}"
    local reason="官方本次修改产生白名单外冲突，需要 AI 逐文件取舍。"
    local tag="${LATEST_TAG:-unknown}"
    local wip_branch="wip-cn-${tag#v}-needs-conflicts"
    local round_now
    round_now="$(handoff_round 2>/dev/null || echo 0)"

    trap - ERR
    set +e

    if [ "$round_now" -ge 3 ]; then
        handoff_failure_menu
        pause_exit 1
    fi

    echo
    echo "⏸  $reason"

    cd "$REPO" 2>/dev/null || { TRANSACTION_ACTIVE=1; fail "$reason"; }

    # Commit the conflicted tree as-is onto a wip branch. Conflict markers are
    # intentional here — they are the input to the AI's decision.
    git add -A >/dev/null 2>&1
    local commit_msg
    commit_msg="$(
        printf '%s\n\n' "$reason"
        printf 'Compositor-CN Updater V%s 自动合并 %s 后停在新冲突。\n' "${VERSION:-?}" "$tag"
        printf '合并结果（含冲突标记）已完整保留，只需逐文件取舍，不必重做合并。\n'
    )"
    if ! git -c user.name='Compositor-CN Updater' \
             -c user.email='local@compositor-cn' \
             commit -q -m "$commit_msg" >/dev/null 2>&1; then
        echo "⚠️ 无法提交冲突树，退回回滚。"
        TRANSACTION_ACTIVE=1
        fail "$reason"
    fi

    local merged_head
    merged_head="$(git rev-parse HEAD)"
    if git show-ref --verify --quiet "refs/heads/$wip_branch"; then
        wip_branch="${wip_branch}-$(date +%H%M%S)"
    fi
    git branch "$wip_branch" "$merged_head" >/dev/null 2>&1

    # Abort the in-progress merge and return to pre-run state.
    git merge --abort >/dev/null 2>&1
    if [ -n "${ORIGINAL_CN_HEAD:-}" ]; then
        git reset --hard "$ORIGINAL_CN_HEAD" >/dev/null 2>&1
    fi
    if [ "${ORIGINAL_SNAPSHOT_EXISTS:-0}" -eq 1 ] && [ -n "${ORIGINAL_SNAPSHOT_HEAD:-}" ]; then
        git branch -f "$SNAPSHOT_BRANCH" "$ORIGINAL_SNAPSHOT_HEAD" >/dev/null 2>&1
    fi
    if [ "${ORIGINAL_SNAPSHOT_TAG_SET:-0}" -eq 1 ]; then
        git config compositor-cn.snapshot-tag "$ORIGINAL_SNAPSHOT_TAG" >/dev/null 2>&1
    else
        git config --unset-all compositor-cn.snapshot-tag >/dev/null 2>&1
    fi

    MERGE_ACTIVE=0
    TRANSACTION_ACTIVE=0
    ROLLBACK_COMPLETE=1
    ROLLBACK_IN_PROGRESS=0

    if [ -n "$conflicts_file" ] && [ -f "$conflicts_file" ]; then
        cp "$conflicts_file" "${STATE_DIR:-/tmp}/last-conflicts.txt" 2>/dev/null || true
        mkdir -p "${STATE_DIR:-/tmp}/handoff/evidence" 2>/dev/null || true
        cp "$conflicts_file" "${STATE_DIR:-/tmp}/handoff/evidence/conflicts.txt" 2>/dev/null || true
    fi

    SNAPSHOT_HEAD="$merged_head^2" write_handoff_bundle \
        "conflicts" "$reason" "${STATE_DIR:-/tmp}/last-conflicts.txt" "$wip_branch"

    echo "✅ 冲突树已停在分支：$wip_branch"
    echo "   到 WorkBuddy 说「继续更新」，AI 逐文件取舍后回来按回车续跑。"
    pause_exit 3
}

# Resume from a handoff. Validates the AI's work, re-runs every gate, and
# restores updater state. Returns 0 only when it is safe to proceed to build.
# On a gate failure it parks a new round (round+1) and returns 1.
resume_from_handoff() {
    trap - ERR
    set +e

    local manifest="$HANDOFF_DIR/manifest.json"
    local done="$HANDOFF_DIR/DONE.json"
    local wip tag round cn_head snap_head snap_tag backup
    wip="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("wip_branch",""))' "$manifest" 2>/dev/null)"
    tag="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("latest_tag",""))' "$manifest" 2>/dev/null)"
    round="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("round",0))' "$manifest" 2>/dev/null)"
    cn_head="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("original_cn_head",""))' "$manifest" 2>/dev/null)"
    snap_head="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("snapshot_branch_head",""))' "$manifest" 2>/dev/null)"
    snap_tag="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("original_snapshot_tag",""))' "$manifest" 2>/dev/null)"
    backup="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("backup_branch",""))' "$manifest" 2>/dev/null)"

    echo
    echo "=== 续跑上次未完成的更新（round $round, tag ${tag}）==="

    cd "$REPO" || return 1

    # --- validation ---
    local cur
    cur="$(git branch --show-current)"
    [ "$cur" = "$wip" ] || { echo "✗ 当前不在 wip 分支（在 ${cur}，应为 ${wip}）"; return 1; }
    [ -z "$(git status --porcelain)" ] || { echo "✗ 工作区不干净"; return 1; }
    [ ! -f .git/MERGE_HEAD ] || { echo "✗ 仍有 MERGE_HEAD"; return 1; }
    if grep -rqiE '^(<<<<<<<|>>>>>>>)' Compositor CompositorTests Compositor.xcodeproj 2>/dev/null; then
        echo "✗ 全树仍有冲突标记"; return 1
    fi
    [ -f "$done" ] || { echo "✗ 未找到 DONE.json，AI 还没写完"; return 1; }
    local done_round
    done_round="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("round",-1))' "$done" 2>/dev/null)"
    [ "$done_round" = "$round" ] || { echo "✗ DONE.json.round ($done_round) != manifest.round ($round)"; return 1; }

    local unresolved
    unresolved="$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1])).get("unresolved",[])))' "$done" 2>/dev/null)"
    if [ "${unresolved:-0}" -gt 0 ]; then
        echo "⚠️ AI 标记了 $unresolved 个未解决项，请人工确认后再续跑。"
        return 1
    fi

    echo "✓ 结构校验通过（在 ${wip}、干净、无冲突标记、DONE round 匹配）"

    # --- re-run gates ---
    local gate_fail=0
    local keys_script="$REPO/tools/localization/audit_keys.py"
    if [ -f "$keys_script" ]; then
        COMPOSITOR_CN_REPO="$REPO" python3 "$keys_script" >/dev/null 2>&1 || gate_fail=1
    fi
    if [ -f "$HANDOFF_DIR/dynamic-english-baseline.txt" ]; then
        DYNAMIC_BASELINE="$HANDOFF_DIR/dynamic-english-baseline.txt"
        scan_dynamic_english "$DYNAMIC_BASELINE" > "$HANDOFF_DIR/evidence/resume-dynamic.txt" 2>/dev/null
        [ -s "$HANDOFF_DIR/evidence/resume-dynamic.txt" ] && gate_fail=1
    fi

    if [ "$gate_fail" -ne 0 ]; then
        echo "✗ 门禁未通过，生成新一轮交接包（round +1）。"
        write_handoff_bundle "resume-gate-failed" \
            "续跑门禁未通过，需要再处理一轮。" \
            "$HANDOFF_DIR/evidence/resume-dynamic.txt" "$wip"
        return 1
    fi
    echo "✓ 门禁重跑通过"

    # --- restore updater state ---
    if [ -n "$snap_head" ] && git rev-parse --verify "$snap_head" >/dev/null 2>&1; then
        git branch -f "$SNAPSHOT_BRANCH" "$snap_head" >/dev/null 2>&1
    fi
    if [ -n "$tag" ]; then
        git config compositor-cn.snapshot-tag "$tag" >/dev/null 2>&1
    fi
    if [ -n "$cn_head" ] && git rev-parse --verify "$cn_head" >/dev/null 2>&1; then
        if ! git merge-base --is-ancestor "$cn_head" HEAD 2>/dev/null; then
            echo "✗ original_cn_head 不是 wip HEAD 的祖先，无法快进"; return 1
        fi
    fi

    # Fast-forward the working branch to the AI's wip head.
    git checkout -q adapt-compositor-1.4.1 2>/dev/null || { echo "✗ 无法切回主分支"; return 1; }
    if ! git merge --ff-only "$wip" >/dev/null 2>&1; then
        echo "✗ 快进主分支到 $wip 失败"; return 1
    fi
    echo "✓ 状态恢复 + 主分支快进完成"

    LATEST_TAG="$tag"
    RESUMED=1
    return 0
}

# Archive the handoff and wip branch after a successful resume/install.
archive_handoff() {
    local stamp
    stamp="$(date +%Y%m%d-%H%M%S)"
    if [ -d "$HANDOFF_DIR" ]; then
        mv "$HANDOFF_DIR" "${HANDOFF_DIR}.done-$stamp" 2>/dev/null || true
    fi
    echo "交接包已归档：${HANDOFF_DIR}.done-${stamp}（wip 分支保留供复核）"
}

# Numbered failure menu — never drop the user into a bare git state.
handoff_failure_menu() {
    echo
    echo "本轮交接已达 3 轮上限，仍未通过门禁。请选择："
    echo "  1) 重试：再给 AI 一轮（重置为 round 1）"
    echo "  2) 中止并自动回滚到更新前状态"
    echo "  3) 保留现场转人工（不动仓库，退出）"
    local ans
    read -r ans || ans=3
    case "$ans" in
        1) python3 - "$HANDOFF_DIR/manifest.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d['round']=0; json.dump(d,open(p,'w'),ensure_ascii=False,indent=2)
PY
           echo "已重置为 round 1，请重新交接处理。" ;;
        2) rollback; echo "已回滚到更新前状态。" ;;
        *) echo "现场保留在：$HANDOFF_DIR 与 wip 分支。退出。" ;;
    esac
}

