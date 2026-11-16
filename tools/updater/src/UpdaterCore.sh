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
    local tag="${LATEST_TAG:-unknown}"
    local wip_branch="wip-cn-${tag#v}-needs-localization"

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
    echo
    echo "接手方式："
    echo "   cd $REPO"
    echo "   git checkout $wip_branch"
    echo "   # 补齐中文本地化，再按 AGENTS.md 第 5 步往下走"
    echo

    pause_exit 3
}

