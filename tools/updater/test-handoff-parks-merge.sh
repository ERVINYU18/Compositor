#!/bin/bash
# Isolated rehearsal for handoff_for_localization. Builds a throwaway repo that
# mimics the real one's shape (CN branch + upstream snapshot branch + snapshot-tag)
# and checks that a localization gate parks the merge instead of discarding it.
set -u

CORE="/Applications/Compositor-CN Updater.app/Contents/Resources/UpdaterCore.sh"
ROOT="/tmp/handoff-rehearsal"
rm -rf "$ROOT"; mkdir -p "$ROOT"; cd "$ROOT" || exit 1

git init -q .
git config user.email t@t; git config user.name t
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

printf 'v1\n' > app.txt
git add -A; git commit -qm 'cn base'
CN_BASE="$(git rev-parse HEAD)"
git branch -m adapt-compositor-1.4.1

# Upstream snapshot branch, one commit ahead of the CN base.
git checkout -q -b compositor-upstream-snapshot
printf 'v1\nupstream\n' > app.txt
printf 'new\n' > newfile.txt
git add -A; git commit -qm 'official snapshot'
SNAP_HEAD="$(git rev-parse HEAD)"

git checkout -q adapt-compositor-1.4.1
git config compositor-cn.snapshot-tag v1.5.6
TAG_BEFORE="$(git config compositor-cn.snapshot-tag)"

# The updater's transaction state, as it stands when a gate fires.
export REPO="$ROOT"
export APP="$ROOT/no-such-app"
export SNAPSHOT_BRANCH=compositor-upstream-snapshot
export LATEST_TAG=v1.5.7
export VERSION=2.2.1
export ORIGINAL_CN_HEAD="$CN_BASE"
export ORIGINAL_SNAPSHOT_EXISTS=1
export ORIGINAL_SNAPSHOT_HEAD="$SNAP_HEAD"
export ORIGINAL_SNAPSHOT_TAG_SET=1
export ORIGINAL_SNAPSHOT_TAG="$TAG_BEFORE"
export BACKUP_BRANCH=""
export MERGE_ACTIVE=0
export TRANSACTION_ACTIVE=1
export ROLLBACK_IN_PROGRESS=0
export ROLLBACK_COMPLETE=0

# shellcheck disable=SC1090
. "$CORE"

# Merge, resolve one conflict by hand (as the CN patch does), leave it staged.
git checkout -q -b compositor-upstream-snapshot-157
git checkout -q adapt-compositor-1.4.1
git merge --no-commit --no-ff compositor-upstream-snapshot >/dev/null 2>&1 || true
git add -A

echo "--- 门禁触发，调用 handoff ---"
# pause_exit 会 exit，必须放进子 shell，否则测试脚本自己也被退出。
( handoff_for_localization "缺少 34 条 zh-Hans 词条，需要补齐翻译。" "/tmp/missing.txt" < /dev/null )
CODE=$?
echo "--- 退出码：$CODE ---"

FAIL=0
chk() { if [ "$2" = "$3" ]; then echo "  ✓ $1"; else echo "  ✗ $1（期望 $3，实际 $2）"; FAIL=1; fi }

echo
echo "=== 断言 ==="
WIP="wip-cn-1.5.7-needs-localization"
chk "wip 分支存在" "$(git show-ref --verify --quiet refs/heads/$WIP && echo yes || echo no)" "yes"
chk "wip 是双亲合并提交" "$(git rev-list --parents -n1 $WIP | wc -w | tr -d ' ')" "3"
chk "当前分支回到更新前 HEAD" "$(git rev-parse HEAD)" "$CN_BASE"
chk "当前分支名未变" "$(git branch --show-current)" "adapt-compositor-1.4.1"
chk "工作区干净" "$(git status --porcelain | wc -l | tr -d ' ')" "0"
chk "无 MERGE_HEAD" "$([ -f .git/MERGE_HEAD ] && echo yes || echo no)" "no"
chk "snapshot-tag 已还原" "$(git config compositor-cn.snapshot-tag)" "$TAG_BEFORE"
chk "snapshot 分支已还原" "$(git rev-parse compositor-upstream-snapshot)" "$SNAP_HEAD"
chk "wip 里含上游新文件" "$(git show $WIP:newfile.txt 2>/dev/null | tr -d '\n')" "new"
chk "wip 里保留了两边内容" "$(git show $WIP:app.txt | tr -d '\n')" "v1upstream"
chk "退出码为 3" "$CODE" "3"

echo
if [ "$FAIL" = 0 ]; then echo "REHEARSAL_OK"; else echo "REHEARSAL_FAILED"; fi
exit "$FAIL"
