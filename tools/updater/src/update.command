#!/bin/bash
set -Eeuo pipefail

VERSION="2.4.0"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

REPO="$HOME/Desktop/AI/AI Project/Compositor CN/Compositor-CN"
APP="/Applications/Compositor-CN.app"
BUILD="$HOME/Library/Caches/Compositor-CN-Build"

STATE_DIR="$HOME/Library/Application Support/Compositor-CN-Updater"
SNAPSHOT_BRANCH="compositor-upstream-snapshot"

API="https://api.github.com/repos/robbietilton/Compositor"

mkdir -p "$STATE_DIR"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/compositor-cn-v2.XXXXXX")"
ZH_BACKUP="$TMP_ROOT/zh-Hans.json"
CONFLICTS_FILE="$TMP_ROOT/conflicts.txt"

DYNAMIC_BASELINE="$TMP_ROOT/dynamic-english-baseline.txt"
DYNAMIC_CURRENT="$TMP_ROOT/dynamic-english-current.txt"
DYNAMIC_REPORT="$STATE_DIR/DynamicEnglish.txt"

CURRENT_BRANCH=""
BACKUP_BRANCH=""
MERGE_ACTIVE=0

# V2.1 transaction state
TRANSACTION_ACTIVE=0
ROLLBACK_IN_PROGRESS=0
ROLLBACK_COMPLETE=0
ORIGINAL_CN_HEAD=""
ORIGINAL_SNAPSHOT_EXISTS=0
ORIGINAL_SNAPSHOT_HEAD=""
ORIGINAL_SNAPSHOT_TAG_SET=0
ORIGINAL_SNAPSHOT_TAG=""
WORKTREE=""

INSTALL_NEW=""
INSTALL_BACKUP=""
INSTALL_OLD_MOVED=0
INSTALL_SWAPPED=0

cleanup() {
    if [ -d "$TMP_ROOT" ]; then
        rm -rf "$TMP_ROOT"
    fi
}
trap cleanup EXIT

. "$SCRIPT_DIR/UpdaterCore.sh"

echo "================================================"
echo " Compositor-CN Updater V${VERSION}"
echo "================================================"
echo

# --------------------------------------------------
# 基础检查
# --------------------------------------------------

[ -d "$REPO/.git" ] || fail "找不到源码仓库：$REPO"

cd "$REPO"

CURRENT_BRANCH="$(git branch --show-current)"

[ -n "$CURRENT_BRANCH" ] || fail "当前 Git 不在正常分支上。"

if [ "$CURRENT_BRANCH" = "$SNAPSHOT_BRANCH" ]; then
    fail "当前误处于官方快照分支，请先切回中文版分支。"
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "当前源码存在未提交修改："
    echo
    git status --short
    fail "为了防止覆盖你的修改，V2.1 已停止更新。"
fi

# 以后重复出现的相同冲突让 Git 自动记住
git config rerere.enabled true
git config rerere.autoupdate true

# --------------------------------------------------
# 当前安装版本
# --------------------------------------------------

LOCAL_VERSION="未安装"
LOCAL_BUILD="-"

if [ -f "$APP/Contents/Info.plist" ]; then
    LOCAL_VERSION="$(
        /usr/libexec/PlistBuddy \
        -c 'Print :CFBundleShortVersionString' \
        "$APP/Contents/Info.plist" 2>/dev/null || echo "未知"
    )"

    LOCAL_BUILD="$(
        /usr/libexec/PlistBuddy \
        -c 'Print :CFBundleVersion' \
        "$APP/Contents/Info.plist" 2>/dev/null || echo "未知"
    )"
fi

echo "当前本地版本：$LOCAL_VERSION ($LOCAL_BUILD)"

# --------------------------------------------------
# GitHub 最新正式 Release
# --------------------------------------------------

echo "正在检查官方正式版…"

RELEASE_JSON="$(
    curl -fsSL \
        --retry 2 \
        --connect-timeout 15 \
        -H "Accept: application/vnd.github+json" \
        "$API/releases/latest"
)" || fail "无法连接 GitHub Release API。"

LATEST_TAG="$(
    printf '%s' "$RELEASE_JSON" |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])'
)"

[ -n "${LATEST_TAG#v}" ] || fail "无法读取官方版本号。"

echo "官方最新版本：${LATEST_TAG#v}"
echo

# --------------------------------------------------
# 如果源码和安装包都已经是最新版，直接结束
# --------------------------------------------------

SNAPSHOT_TAG="$(git config --get compositor-cn.snapshot-tag 2>/dev/null || true)"

if [ "$LOCAL_VERSION" = "${LATEST_TAG#v}" ] &&
   [ "$SNAPSHOT_TAG" = "$LATEST_TAG" ] &&
   git show-ref --verify --quiet "refs/heads/$SNAPSHOT_BRANCH" &&
   git merge-base --is-ancestor "$SNAPSHOT_BRANCH" HEAD 2>/dev/null; then

    echo "✅ 当前已经包含官方最新版。"
    pause_exit 0
fi

# --------------------------------------------------
# V2.1：建立完整事务恢复点
# --------------------------------------------------

ORIGINAL_CN_HEAD="$(git rev-parse HEAD)"

if git show-ref --verify --quiet "refs/heads/$SNAPSHOT_BRANCH"; then
    ORIGINAL_SNAPSHOT_EXISTS=1
    ORIGINAL_SNAPSHOT_HEAD="$(git rev-parse "$SNAPSHOT_BRANCH")"
else
    ORIGINAL_SNAPSHOT_EXISTS=0
    ORIGINAL_SNAPSHOT_HEAD=""
fi

if ORIGINAL_SNAPSHOT_TAG="$(
    git config --get compositor-cn.snapshot-tag 2>/dev/null
)"; then
    ORIGINAL_SNAPSHOT_TAG_SET=1
else
    ORIGINAL_SNAPSHOT_TAG_SET=0
    ORIGINAL_SNAPSHOT_TAG=""
fi

TRANSACTION_ACTIVE=1

echo "✅ 已建立 V2.1 更新事务恢复点"

scan_dynamic_english "$DYNAMIC_BASELINE" >/dev/null

# --------------------------------------------------
# 保存现有中文翻译
# --------------------------------------------------

CATALOG="$REPO/Compositor/Localizable.xcstrings"

if [ -f "$CATALOG" ]; then
    python3 - "$CATALOG" "$ZH_BACKUP" <<'PY'
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])

data = json.loads(src.read_text())
saved = {}

for key, item in data.get("strings", {}).items():
    zh = item.get("localizations", {}).get("zh-Hans")
    if zh is not None:
        saved[key] = zh

out.write_text(
    json.dumps(saved, ensure_ascii=False, indent=2)
)

print(f"已保护 {len(saved)} 条简体中文翻译。")
PY
fi

# --------------------------------------------------
# 下载官方 Release Tag 源码
# --------------------------------------------------

echo
echo "正在下载官方 $LATEST_TAG 源码…"

TARBALL="$TMP_ROOT/source.tar.gz"
SOURCE_DIR="$TMP_ROOT/source"

mkdir -p "$SOURCE_DIR"

curl -fL \
    --retry 2 \
    --connect-timeout 15 \
    "$API/tarball/$LATEST_TAG" \
    -o "$TARBALL" || fail "官方源码下载失败。"

tar -xzf "$TARBALL" \
    -C "$SOURCE_DIR" \
    --strip-components=1 || fail "官方源码解压失败。"

echo "✅ 下载完成"

# --------------------------------------------------
# 更新官方快照分支
# --------------------------------------------------

echo
echo "正在准备官方源码快照…"

if ! git show-ref --verify --quiet "refs/heads/$SNAPSHOT_BRANCH"; then
    git branch "$SNAPSHOT_BRANCH" "$CURRENT_BRANCH"
fi

WORKTREE="$TMP_ROOT/worktree"

git worktree add \
    "$WORKTREE" \
    "$SNAPSHOT_BRANCH" >/dev/null || fail "无法创建官方快照工作区。"

rsync -a \
    --delete \
    --exclude='.git' \
    "$SOURCE_DIR/" \
    "$WORKTREE/" || fail "同步官方源码失败。"

git -C "$WORKTREE" add -A

if ! git -C "$WORKTREE" diff --cached --quiet; then
    git -C "$WORKTREE" \
        -c user.name="Compositor-CN Updater" \
        -c user.email="local@compositor-cn" \
        commit -m "Official snapshot $LATEST_TAG" >/dev/null \
        || fail "无法生成官方源码快照。"
fi

git worktree remove "$WORKTREE" --force >/dev/null

git config compositor-cn.snapshot-tag "$LATEST_TAG"

# --------------------------------------------------
# 创建安全备份
# --------------------------------------------------

cd "$REPO"

BACKUP_BRANCH="backup-cn-v2-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH" HEAD

echo "✅ 已创建安全备份：$BACKUP_BRANCH"

# --------------------------------------------------
# 合并
# --------------------------------------------------

# 防止后续流程中版本变量意外丢失
echo
echo "正在自动合并 ${LATEST_TAG#v}…"

if git merge \
    --no-commit \
    --no-ff \
    "$SNAPSHOT_BRANCH"; then
    MERGE_RESULT=0
else
    MERGE_RESULT=$?
fi

MERGE_ACTIVE=1

git diff \
    --name-only \
    --diff-filter=U > "$CONFLICTS_FILE"

if [ "$MERGE_RESULT" -ne 0 ] && [ ! -s "$CONFLICTS_FILE" ]; then
    fail "Git 合并异常退出且没有可处理冲突，已停止更新。"
fi

# --------------------------------------------------
# 判断冲突是否属于 V2 可自动处理范围
# --------------------------------------------------

UNKNOWN_CONFLICTS=""

while IFS= read -r file; do
    [ -z "$file" ] && continue

    case "$file" in
        "Compositor.xcodeproj/project.pbxproj"|"Compositor/CompositorApp.swift"|"Compositor/UI/BlendModePicker.swift"|"Compositor/Localizable.xcstrings")
            ;;
        *)
            UNKNOWN_CONFLICTS="${UNKNOWN_CONFLICTS}${file}"$'\n'
            ;;
    esac
done < "$CONFLICTS_FILE"

if [ -n "$UNKNOWN_CONFLICTS" ]; then
    echo
    echo "⚠️ 官方本次修改涉及新的冲突位置："
    echo
    printf '%s' "$UNKNOWN_CONFLICTS"

    cp "$CONFLICTS_FILE" \
       "$STATE_DIR/last-conflicts.txt"

    rollback

    echo
    echo "当前稳定版没有受到影响。"
    echo
    echo "冲突清单已保存到："
    echo "$STATE_DIR/last-conflicts.txt"
    echo
    echo "把上面的冲突文件发给 ChatGPT 即可继续处理。"

    pause_exit 1
fi

# --------------------------------------------------
# 已知冲突先采用官方新代码
# 然后重新应用中文版固定规则
# --------------------------------------------------

while IFS= read -r file; do
    [ -z "$file" ] && continue
    git checkout --theirs -- "$file"
done < "$CONFLICTS_FILE"

PATCH_RESULT=0
# V2.4.0: a stale patch rule must leave a handoff trace, not a misleading
# APP_PATCH_FAILED with last-conflicts.txt still holding last round's data.
: > "$STATE_DIR/patch-drift.txt" 2>/dev/null || true

if REPO="$REPO" \
ZH_BACKUP="$ZH_BACKUP" \
CONFLICTS_FILE="$CONFLICTS_FILE" \
STATE_DIR="$STATE_DIR" \
python3 <<'PY'
import json
import os
import re
from pathlib import Path

repo = Path(os.environ["REPO"])
conflicts_path = Path(os.environ["CONFLICTS_FILE"])

conflicts = set()

if conflicts_path.exists():
    conflicts = set(
        x.strip()
        for x in conflicts_path.read_text().splitlines()
        if x.strip()
    )

# ==================================================
# project.pbxproj
# ==================================================

p = repo / "Compositor.xcodeproj/project.pbxproj"
s = p.read_text()

if '"zh-Hans",' not in s:
    marker = """knownRegions = (
				en,
"""

    replacement = """knownRegions = (
				en,
				"zh-Hans",
"""

    if marker not in s:
        raise SystemExit("PROJECT_PATCH_FAILED: knownRegions")

    s = s.replace(marker, replacement, 1)

official_id = "PRODUCT_BUNDLE_IDENTIFIER = com.wonderassembly.compositor;"
cn_id = "PRODUCT_BUNDLE_IDENTIFIER = com.wonderassembly.compositor.cn;"

if official_id in s:
    s = s.replace(official_id, cn_id)

if s.count(cn_id) != 2:
    raise SystemExit(
        f"PROJECT_PATCH_FAILED: Bundle ID count={s.count(cn_id)}"
    )

# V2.4.0: restore the App target's ad-hoc signing settings. Every upstream
# merge brings its own pbxproj and overwrites these. Only the App target's
# Debug and Release blocks are touched; tests/uitests keep their team ID.
app_debug = "8F311FBB304F03BC0017D14F"
app_release = "8F311FBC304F03BC0017D14F"
for block_id in (app_debug, app_release):
    start = s.find(block_id + " /*")
    if start < 0:
        raise SystemExit(f"SIGNING_PATCH_FAILED: missing block {block_id}")
    end = s.find("\n\t\t};", start)
    if end < 0:
        raise SystemExit(f"SIGNING_PATCH_FAILED: unterminated block {block_id}")
    block = s[start:end]

    # Normalize CODE_SIGN_IDENTITY whether present or absent. Upstream's
    # Automatic style can carry "Apple Development" here; normalizing only a
    # missing key would leave a bad identity in place and fail the Release
    # build later. Add beside CODE_SIGN_ENTITLEMENTS when absent.
    if "CODE_SIGN_IDENTITY" in block:
        block = re.sub(
            r'CODE_SIGN_IDENTITY = [^;]*;',
            'CODE_SIGN_IDENTITY = "-";',
            block,
        )
    else:
        anchor = "CODE_SIGN_ENTITLEMENTS = Config/Compositor.entitlements;"
        if anchor not in block:
            raise SystemExit(f"SIGNING_PATCH_FAILED: no anchor in {block_id}")
        block = block.replace(
            anchor,
            anchor + '\n\t\t\t\tCODE_SIGN_IDENTITY = "-";',
            1,
        )

    block = re.sub(
        r'CODE_SIGN_STYLE = [^;]+;',
        'CODE_SIGN_STYLE = Manual;',
        block,
    )
    block = re.sub(
        r'DEVELOPMENT_TEAM = [^;]*;',
        'DEVELOPMENT_TEAM = "";',
        block,
    )
    block = re.sub(
        r'ENABLE_HARDENED_RUNTIME = [^;]+;',
        'ENABLE_HARDENED_RUNTIME = NO;',
        block,
    )
    s = s[:start] + block + s[end:]

p.write_text(s)

# ==================================================
# CompositorApp.swift
# ==================================================

p = repo / "Compositor/CompositorApp.swift"
s = p.read_text()

# 禁用官方 Sparkle 的菜单入口
pattern = re.compile(
    r'\n\s*CommandGroup\(after: \.appInfo\) \{\s*'
    r'Button\("Check for Updates…"\) '
    r'\{ applicationDelegate\.updater\.checkForUpdates\(nil\) \}\s*'
    r'\}\n',
    re.S
)

s = pattern.sub("\n", s, count=1)

old = '''                        Button(session.history.canUndo ? "Undo \\(session.history.undoName)" : "Undo") { session.undo() }
                            .configuredKeyboardShortcut("z").disabled(!session.canUndo)
                        Button(session.history.canRedo ? "Redo \\(session.history.redoName)" : "Redo") { session.redo() }
                            .configuredKeyboardShortcut("z", modifiers: [.command, .shift]).disabled(!session.canRedo)'''

new = '''                        Button(session.history.canUndo
                            ? String(format: localizedString("Undo %@"), localizedHistoryAction(session.history.undoName))
                            : localizedString("Undo")) { session.undo() }
                            .configuredKeyboardShortcut("z").disabled(!session.canUndo)
                        Button(session.history.canRedo
                            ? String(format: localizedString("Redo %@"), localizedHistoryAction(session.history.redoName))
                            : localizedString("Redo")) { session.redo() }
                            .configuredKeyboardShortcut("z", modifiers: [.command, .shift]).disabled(!session.canRedo)'''

if old in s:
    s = s.replace(old, new, 1)

s = s.replace(
    'Button("\\(kind.rawValue)…")',
    'Button(kind.localizedName + "…")'
)

s = s.replace(
    'Button(kind.rawValue + (kind.isEditable ? "…" : "")) { session.addAdjustment(kind) }',
    'Button(kind.localizedName + (kind.isEditable ? "…" : "")) { session.addAdjustment(kind) }'
)

s = s.replace(
    'Button(session.mergeTitle) { session.mergeLayers() }',
    'Button(localizedString(session.mergeTitle)) { session.mergeLayers() }'
)

old_delete = '''Button(session.selectedEffect != nil ? "Delete " + session.selectedEffect!.kind.rawValue : session.isMaskSelected && session.activeLayer?.mask != nil ? "Delete Layer Mask" : session.selectedLayerIDs.count > 1 ? "Delete Layers" : "Delete Layer") {'''

new_delete = '''Button(session.selectedEffect != nil
                        ? String(format: localizedString("Delete %@"), session.selectedEffect!.kind.localizedName)
                        : localizedString(session.isMaskSelected && session.activeLayer?.mask != nil ? "Delete Layer Mask" : session.selectedLayerIDs.count > 1 ? "Delete Layers" : "Delete Layer")) {'''

if old_delete in s:
    s = s.replace(old_delete, new_delete, 1)

# 如果这是冲突文件，则必须确认中文版关键规则确实恢复成功
if "Compositor/CompositorApp.swift" in conflicts:
    bad = [
        'Check for Updates…',
        'Undo \\(session.history.undoName)',
        'Redo \\(session.history.redoName)',
        'Button("\\(kind.rawValue)…")',
        'Button(kind.rawValue +',
        'Button(session.mergeTitle)'
    ]

    remains = [x for x in bad if x in s]

    if remains:
        # V2.4.0: the upstream text changed, so the exact-match replacements
        # silently skipped. This is a handoff case, not a bare integrity
        # failure: leave a fresh trace instead of reusing a stale conflict
        # list and reporting a misleading generic error.
        drift = Path(os.environ.get("STATE_DIR", ".")) / "patch-drift.txt"
        drift.write_text(
            "APP_PATCH_DRIFT: upstream source changed; the following "
            "Chinese rules were not restored:\n" + "\n".join(remains) + "\n"
        )
        raise SystemExit(
            "APP_PATCH_DRIFT: " + ", ".join(remains)
        )

p.write_text(s)

# ==================================================
# BlendModePicker.swift
# ==================================================

p = repo / "Compositor/UI/BlendModePicker.swift"
s = p.read_text()

old = '''            for mode in group { button.addItem(withTitle: mode.rawValue) }'''

new = '''            for mode in group {
                button.addItem(withTitle: mode.localizedName)
                if let item = button.lastItem,
                   let modeIndex = LayerBlendMode.allCases.firstIndex(of: mode) {
                    item.tag = modeIndex
                }
            }'''

if old in s:
    s = s.replace(old, new, 1)

s = s.replace(
    'button.setAccessibilityLabel("Blend mode")',
    'button.setAccessibilityLabel(localizedString("Blend mode"))'
)

old = '''            button.selectItem(withTitle: (session.activeLayer?.blendMode ?? .normal).rawValue)'''

new = '''            let mode = session.activeLayer?.blendMode ?? .normal
            if let modeIndex = LayerBlendMode.allCases.firstIndex(of: mode) {
                let menuIndex = button.indexOfItem(withTag: modeIndex)
                if menuIndex >= 0 { button.selectItem(at: menuIndex) }
            }'''

if old in s:
    s = s.replace(old, new, 1)

old = '''            guard let mode = item.flatMap({ LayerBlendMode(rawValue: $0.title) }) else { return }
            highlightedMode = mode'''

new = '''            guard let item,
                  !item.isSeparatorItem,
                  LayerBlendMode.allCases.indices.contains(item.tag) else { return }
            let mode = LayerBlendMode.allCases[item.tag]
            highlightedMode = mode'''

if old in s:
    s = s.replace(old, new, 1)

old = '''            guard session.activeLayerID == layerID,
                  let mode = highlightedMode ?? button.selectedItem.flatMap({ LayerBlendMode(rawValue: $0.title) }) else { return }
            session.setLayerBlendMode(mode)
            button.selectItem(withTitle: mode.rawValue)'''

new = '''            let selectedMode: LayerBlendMode?
            if let highlightedMode {
                selectedMode = highlightedMode
            } else if let item = button.selectedItem,
                      !item.isSeparatorItem,
                      LayerBlendMode.allCases.indices.contains(item.tag) {
                selectedMode = LayerBlendMode.allCases[item.tag]
            } else {
                selectedMode = nil
            }

            guard session.activeLayerID == layerID,
                  let mode = selectedMode else { return }

            session.setLayerBlendMode(mode)

            if let modeIndex = LayerBlendMode.allCases.firstIndex(of: mode) {
                let menuIndex = button.indexOfItem(withTag: modeIndex)
                if menuIndex >= 0 { button.selectItem(at: menuIndex) }
            }'''

if old in s:
    s = s.replace(old, new, 1)

if "Compositor/UI/BlendModePicker.swift" in conflicts:
    forbidden = [
        "addItem(withTitle: mode.rawValue)",
        "LayerBlendMode(rawValue: $0.title)",
        "selectItem(withTitle: mode.rawValue)"
    ]

    remains = [x for x in forbidden if x in s]

    if remains:
        # V2.4.0: same handoff case as APP_PATCH_DRIFT — upstream changed its
        # source text so the exact-match replacement skipped. Leave a fresh
        # trace instead of a generic hard stop with a stale conflict list.
        drift = Path(os.environ.get("STATE_DIR", ".")) / "patch-drift.txt"
        with drift.open("a", encoding="utf-8") as fh:
            fh.write(
                "BLEND_PATCH_DRIFT: upstream source changed; the following "
                "Chinese rules were not restored:\n" + "\n".join(remains) + "\n"
            )
        raise SystemExit(
            "BLEND_PATCH_DRIFT: " + ", ".join(remains)
        )

p.write_text(s)

# ==================================================
# 恢复已有 zh-Hans 翻译
# ==================================================

catalog = repo / "Compositor/Localizable.xcstrings"
backup = Path(os.environ["ZH_BACKUP"])

if catalog.exists() and backup.exists():
    data = json.loads(catalog.read_text())
    saved = json.loads(backup.read_text())

    strings = data.setdefault("strings", {})

    for key, zh in saved.items():
        item = strings.setdefault(key, {})
        item.setdefault("localizations", {})["zh-Hans"] = zh

    catalog.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )

print("CN_PATCH_OK")
PY
then
    PATCH_RESULT=0
else
    PATCH_RESULT=$?
fi

if [ "$PATCH_RESULT" -ne 0 ]; then
    # V2.4.0: patch drift means upstream changed its source text. Leave a
    # fresh handoff trace and say so plainly, rather than a generic error
    # that points at last round's last-conflicts.txt.
    if [ -s "$STATE_DIR/patch-drift.txt" ]; then
        cp "$STATE_DIR/patch-drift.txt" "$STATE_DIR/last-conflicts.txt"
        fail "上游原文已变，中文规则未能自动恢复，需要 AI 接手（见 last-conflicts.txt）。当前稳定版未受影响。"
    fi
    fail "自动恢复中文版定制失败，当前稳定版未受影响。"
fi

git add -A

if [ -n "$(git diff --name-only --diff-filter=U)" ]; then
    git diff --name-only --diff-filter=U \
        > "$STATE_DIR/last-conflicts.txt"

    fail "仍存在未解决冲突，已自动恢复稳定版。"
fi

echo "✅ 已自动处理已知冲突"
echo "✅ 已恢复中文版固定设置"
echo "✅ 已恢复现有简体中文翻译"

# --------------------------------------------------
# V2.1：检查新增明显动态英文
# --------------------------------------------------

scan_dynamic_english "$DYNAMIC_CURRENT" >/dev/null

python3 - \
    "$DYNAMIC_BASELINE" \
    "$DYNAMIC_CURRENT" \
    "$DYNAMIC_REPORT" <<'PY_DYNAMIC'
import sys
from pathlib import Path

baseline_path = Path(sys.argv[1])
current_path = Path(sys.argv[2])
report_path = Path(sys.argv[3])

def load(path):
    result = {}
    if not path.exists():
        return result

    for raw in path.read_text().splitlines():
        if "\t" not in raw:
            continue

        signature, display = raw.split("\t", 1)
        result[signature] = display

    return result

baseline = load(baseline_path)
current = load(current_path)

new_items = [
    current[key]
    for key in sorted(current)
    if key not in baseline
]

report_path.write_text(
    "\n".join(new_items) + ("\n" if new_items else ""),
    encoding="utf-8"
)

print(len(new_items))
PY_DYNAMIC

DYNAMIC_NEW_COUNT="$(
    [ -f "$DYNAMIC_REPORT" ] &&
    awk 'NF { n++ } END { print n+0 }' "$DYNAMIC_REPORT" ||
    echo 0
)"

if [ "$DYNAMIC_NEW_COUNT" -gt 0 ]; then
    echo
    echo "⚠️ 检测到 $DYNAMIC_NEW_COUNT 个新增动态英文风险："
    echo
    cat "$DYNAMIC_REPORT"
    echo
    echo "清单：$DYNAMIC_REPORT"

    handoff_for_localization \
        "发现 $DYNAMIC_NEW_COUNT 个新增动态 UI 英文模式，需要人工确认。" \
        "$DYNAMIC_REPORT"
fi

echo "✅ 未发现新增明显动态英文"

# --------------------------------------------------
# 检查可能新增但尚未翻译的字符串
# --------------------------------------------------

MISSING_FILE="$STATE_DIR/MissingTranslations.txt"

check_missing_zh_hans "$CATALOG" "$MISSING_FILE"

MISSING_COUNT="$(
    [ -f "$MISSING_FILE" ] &&
    awk 'NF { n++ } END { print n+0 }' "$MISSING_FILE" ||
    echo 0
)"

if [ "$MISSING_COUNT" -gt 0 ]; then
    echo
    echo "⚠️ 检测到 $MISSING_COUNT 个尚未中文化的字符串："
    echo
    cat "$MISSING_FILE"
    echo
    echo "清单：$MISSING_FILE"

    handoff_for_localization \
        "缺少 $MISSING_COUNT 条 zh-Hans 词条，需要补齐翻译。" \
        "$MISSING_FILE"
fi

echo "✅ Localizable.xcstrings 的 zh-Hans 翻译完整"

# --------------------------------------------------
# V2.4.0: audit the key-carrier blind spots that audit_strings.py cannot see
# (LocalizedStringKey switch bodies and ternary branches). The `Text` layer
# key went missing for four rounds because nothing checked these.
# --------------------------------------------------

AUDIT_KEYS_SCRIPT="$REPO/tools/localization/audit_keys.py"
if [ -f "$AUDIT_KEYS_SCRIPT" ]; then
    KEYS_REPORT="$STATE_DIR/audit-keys-gaps.txt"
    # UpdaterCore.sh installs an ERR trap under `set -Eeuo pipefail`. A bare
    # nonzero python exit would fire that trap and roll back the whole merge
    # before we could hand it off. Absorb the status so this gate stays a
    # handoff rather than becoming an accidental rollback.
    KEYS_RESULT=0
    COMPOSITOR_CN_REPO="$REPO" python3 "$AUDIT_KEYS_SCRIPT" > "$STATE_DIR/audit-keys.log" 2>&1 || KEYS_RESULT=$?

    if [ "$KEYS_RESULT" -ne 0 ]; then
        # Extract the human-readable gap section for the handoff report.
        sed -n '/--- LocalizedStringKey-carried/,/^$/p' "$STATE_DIR/audit-keys.log" \
            > "$KEYS_REPORT" 2>/dev/null || true
        sed -n '/--- ternary-carried/,/^$/p' "$STATE_DIR/audit-keys.log" \
            >> "$KEYS_REPORT" 2>/dev/null || true
        [ -s "$KEYS_REPORT" ] || cp "$STATE_DIR/audit-keys.log" "$KEYS_REPORT"

        handoff_for_localization \
            "LocalizedStringKey / 三元表达式承载的界面字面量缺少词条，需要补齐。" \
            "$KEYS_REPORT"
    fi

    echo "✅ 键承载盲区审计通过"
else
    echo "⚠️ 未找到 $AUDIT_KEYS_SCRIPT，跳过键承载盲区审计"
fi

# --------------------------------------------------
# 编译测试版
# --------------------------------------------------

echo
echo "正在编译 Compositor-CN ${LATEST_TAG#v}…"

rm -rf "$BUILD"

set +e

xcodebuild \
    -project Compositor.xcodeproj \
    -scheme Compositor \
    -configuration Release \
    -derivedDataPath "$BUILD" \
    build 2>&1 | tee "$STATE_DIR/last-build.log"

BUILD_RESULT=${PIPESTATUS[0]}

set -e

if [ "$BUILD_RESULT" -ne 0 ]; then
    fail "编译失败，已经自动恢复到更新前版本。"
fi

TEST_APP="$BUILD/Build/Products/Release/Compositor.app"

[ -d "$TEST_APP" ] || {
    fail "编译成功但找不到生成的 Compositor.app。"
}

TEST_VERSION="$(
    /usr/libexec/PlistBuddy \
        -c 'Print :CFBundleShortVersionString' \
        "$TEST_APP/Contents/Info.plist"
)"

TEST_BUILD="$(
    /usr/libexec/PlistBuddy \
        -c 'Print :CFBundleVersion' \
        "$TEST_APP/Contents/Info.plist"
)"

TEST_BUNDLE="$(
    /usr/libexec/PlistBuddy \
        -c 'Print :CFBundleIdentifier' \
        "$TEST_APP/Contents/Info.plist"
)"

if [ "$TEST_BUNDLE" != "com.wonderassembly.compositor.cn" ]; then
    fail "安全检查失败：生成 App 的 Bundle ID 不正确。"
fi

echo
echo "================================================"
echo " ✅ 编译成功"
echo "================================================"
echo "版本：$TEST_VERSION"
echo "构建：$TEST_BUILD"
echo "Bundle ID：$TEST_BUNDLE"
echo

# --------------------------------------------------
# 直接启动测试版，避免 macOS 打开旧安装包
# --------------------------------------------------

killall Compositor 2>/dev/null || true

"$TEST_APP/Contents/MacOS/Compositor" \
    > "$STATE_DIR/test-app.log" 2>&1 &

echo "已启动测试版。"
echo
echo "请简单检查："
echo "  • 关于 Compositor 的版本"
echo "  • 中文界面"
echo "  • 本次官方新增功能"
echo "  • 菜单中没有官方 Check for Updates…"
echo

read -r -p "测试正常并安装正式版？输入 y 安装，其他键取消： " ANSWER

ANSWER_LOWER="$(
    printf '%s' "$ANSWER" |
    tr '[:upper:]' '[:lower:]'
)"

if [ "$ANSWER_LOWER" != "y" ] &&
   [ "$ANSWER_LOWER" != "yes" ]; then

    rollback

    echo
    echo "已取消安装。"
    echo "当前 /Applications/Compositor-CN.app 保持原版本不变。"

    pause_exit 0
fi

# --------------------------------------------------
# 正式提交源码
# --------------------------------------------------

killall Compositor 2>/dev/null || true

cd "$REPO"

git add -A

git \
    -c user.name="Compositor-CN Updater" \
    -c user.email="local@compositor-cn" \
    commit -m "Update Chinese build to Compositor ${LATEST_TAG#v}" \
    >/dev/null ||
        fail "源码提交失败，已恢复更新前状态。"

MERGE_ACTIVE=0

# --------------------------------------------------
# 安装到 /Applications
# --------------------------------------------------

echo
echo "正在事务化安装 Compositor-CN ${LATEST_TAG#v}…"

install_app_transaction "$TEST_APP" "$TEST_VERSION" "$TEST_BUILD"
echo "✅ 新正式版安装校验通过"
defaults write \
    com.wonderassembly.compositor.cn \
    AppleLanguages \
    -array "zh-Hans"

# The transaction left the old app beside /Applications as .rollback.<pid>.
# Keep that path until the transaction is committed below — the rollback
# handler needs it. Archiving happens after TRANSACTION_ACTIVE=0.
ROLLBACK_SOURCE="$INSTALL_BACKUP"

INSTALL_OLD_MOVED=0
INSTALL_SWAPPED=0
INSTALL_NEW=""
INSTALL_BACKUP=""

# 源码和正式 App 都已经成功，事务至此正式提交
TRANSACTION_ACTIVE=0
MERGE_ACTIVE=0

# V2.4.0: archive the old app now that the transaction is committed. This is
# housekeeping, not part of the transaction — a failure here must NOT fire
# the ERR trap and roll back an already-verified install. Every step is
# therefore guarded; the old app is simply left in place if archiving fails.
if [ -d "$ROLLBACK_SOURCE" ]; then
    BACKUP_DIR="$HOME/Desktop/AI/AI Project/Compositor CN/.Compositor-CN-Backups/pre-${LATEST_TAG#v}-install-$(date +%Y%m%d-%H%M%S)"
    if mkdir -p "$BACKUP_DIR" 2>/dev/null; then
        OLD_VER="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$ROLLBACK_SOURCE/Contents/Info.plist" 2>/dev/null || echo unknown)"
        if sudo mv "$ROLLBACK_SOURCE" "$BACKUP_DIR/Compositor-CN-${OLD_VER}.app"; then
            sudo chown -R "$(id -u):$(id -g)" "$BACKUP_DIR" 2>/dev/null || true
            echo "✅ 旧版已归档为回滚点：$BACKUP_DIR/Compositor-CN-${OLD_VER}.app"
        else
            echo "⚠️ 旧版未能归档，仍留在：$ROLLBACK_SOURCE"
        fi
    else
        echo "⚠️ 无法创建归档目录，旧版仍留在：$ROLLBACK_SOURCE"
    fi
fi

# 成功后安全备份分支不再需要
git branch -D "$BACKUP_BRANCH" >/dev/null 2>&1 || true

echo
echo "================================================"
echo " ✅ 更新完成"
echo "================================================"
echo "Compositor-CN：$TEST_VERSION ($TEST_BUILD)"
echo

open "$APP"

pause_exit 0
