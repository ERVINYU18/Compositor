#!/bin/bash
# Rehearsal 2: an unresolved conflict must NOT be committed. The gate has to fall
# back to the old rollback path, leaving no wip branch and a clean tree.
set -u

CORE="/Applications/Compositor-CN Updater.app/Contents/Resources/UpdaterCore.sh"
ROOT="/tmp/handoff-rehearsal2"
rm -rf "$ROOT"; mkdir -p "$ROOT"; cd "$ROOT" || exit 1

git init -q .
git config user.email t@t; git config user.name t
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

printf 'v1\n' > app.txt
git add -A; git commit -qm 'cn base'
git branch -m adapt-compositor-1.4.1

# Upstream edits app.txt one way.
git checkout -q -b compositor-upstream-snapshot
printf 'v1-upstream\n' > app.txt
git add -A; git commit -qm 'official snapshot'
SNAP_HEAD="$(git rev-parse HEAD)"

# The CN branch edits the same line another way, so the merge really conflicts.
git checkout -q adapt-compositor-1.4.1
printf 'v1-cn\n' > app.txt
git add -A; git commit -qm 'cn tweak'
CN_BASE="$(git rev-parse HEAD)"
git config compositor-cn.snapshot-tag v1.5.6

export REPO="$ROOT" APP="$ROOT/no-such-app"
export SNAPSHOT_BRANCH=compositor-upstream-snapshot LATEST_TAG=v1.5.7 VERSION=2.2.1
export ORIGINAL_CN_HEAD="$CN_BASE" ORIGINAL_SNAPSHOT_EXISTS=1 ORIGINAL_SNAPSHOT_HEAD="$SNAP_HEAD"
export ORIGINAL_SNAPSHOT_TAG_SET=1 ORIGINAL_SNAPSHOT_TAG=v1.5.6 BACKUP_BRANCH=""
export MERGE_ACTIVE=0 TRANSACTION_ACTIVE=1 ROLLBACK_IN_PROGRESS=0 ROLLBACK_COMPLETE=0

# shellcheck disable=SC1090
. "$CORE"

git merge --no-commit --no-ff compositor-upstream-snapshot >/dev/null 2>&1 || true
echo "未解决条目：$(git diff --name-only --diff-filter=U | tr '\n' ' ')"

echo "--- 未解决冲突，调用 handoff（应退回回滚）---"
( handoff_for_localization "缺少词条。" "/tmp/missing.txt" < /dev/null )
CODE=$?
echo "--- 退出码：$CODE ---"

FAIL=0
chk() { if [ "$2" = "$3" ]; then echo "  ✓ $1"; else echo "  ✗ $1（期望 $3，实际 $2）"; FAIL=1; fi }

echo
echo "=== 断言 ==="
chk "没有创建 wip 分支" "$(git show-ref --verify --quiet refs/heads/wip-cn-1.5.7-needs-localization && echo yes || echo no)" "no"
chk "回到更新前 HEAD" "$(git rev-parse HEAD)" "$CN_BASE"
chk "工作区干净" "$(git status --porcelain | wc -l | tr -d ' ')" "0"
chk "无 MERGE_HEAD" "$([ -f .git/MERGE_HEAD ] && echo yes || echo no)" "no"
chk "snapshot-tag 已还原" "$(git config compositor-cn.snapshot-tag)" "v1.5.6"
chk "snapshot 分支已还原" "$(git rev-parse compositor-upstream-snapshot)" "$SNAP_HEAD"
chk "app.txt 恢复为 CN 版" "$(cat app.txt | tr -d '\n')" "v1-cn"
chk "app.txt 无冲突标记" "$(grep -c '<<<<<<<' app.txt)" "0"
chk "退出码为 1（回滚）" "$CODE" "1"

echo
if [ "$FAIL" = 0 ]; then echo "REHEARSAL2_OK"; else echo "REHEARSAL2_FAILED"; fi
exit "$FAIL"
