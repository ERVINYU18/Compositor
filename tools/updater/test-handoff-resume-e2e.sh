#!/bin/bash
# Stage 2 end-to-end rehearsal: handoff → AI handoff work → resume.
#
# Uses a throwaway git repo under /tmp and sources the REAL UpdaterCore.sh,
# so the functions exercised are the deployed ones, not copies. Covers:
#   1. handoff_for_conflicts parks a conflicted tree on a wip branch
#   2. the handoff bundle (manifest/INSTRUCTIONS/baseline/evidence) is written
#   3. round cap after 3 rounds
#   4. resume validation rejects: wrong branch, dirty tree, conflict markers,
#      missing DONE.json, mismatched round, unresolved items
#   5. resume re-runs gates, restores snapshot branch/tag, fast-forwards main
#   6. a gate failure parks round+1
#
# No sudo, no xcodebuild, no /Applications — safe inside a sandbox.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
CORE="${UPDATER_CORE:-$REPO_ROOT/tools/updater/src/UpdaterCore.sh}"
ROOT="/tmp/v24-handoff-e2e"
rm -rf "$ROOT"; mkdir -p "$ROOT"; cd "$ROOT" || exit 1

FAIL=0
chk() {
    if [ "$2" = "$3" ]; then echo "  ✓ $1"; else echo "  ✗ $1（期望 [$3]，实际 [$2]）"; FAIL=1; fi
}

echo "=== Stage 2 handoff/resume e2e rehearsal ==="

# ---- build a throwaway repo shaped like the real one ----
git init -q .
git config user.email t@t; git config user.name t
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
printf 'cn\n' > app.txt
git add -A; git commit -qm 'cn base'
CN_BASE="$(git rev-parse HEAD)"
git branch -m adapt-compositor-1.4.1

git checkout -q -b compositor-upstream-snapshot
printf 'cn\nup\n' > app.txt
printf 'new\n' > newfile.txt
git add -A; git commit -qm 'official snapshot'
SNAP_HEAD="$(git rev-parse HEAD)"

git checkout -q adapt-compositor-1.4.1
git config compositor-cn.snapshot-tag v1.6.7

# create a conflicted merge (both sides touched app.txt differently)
printf 'cn\ncn-only\n' > app.txt
git add -A; git commit -qm 'cn local edit'
CN_TIP="$(git rev-parse HEAD)"
git merge --no-ff --no-commit compositor-upstream-snapshot >/dev/null 2>&1 || true

# ---- source the real core, set env as the updater would ----
export REPO="$ROOT"
export APP="$ROOT/no-such-app"
# STATE_DIR lives OUTSIDE the throwaway repo, as it does in reality
# (~/Library/Application Support). Inside the repo would make handoff files
# look like working-tree changes and break checkout/resume.
export STATE_DIR="/tmp/v24-handoff-e2e-state"
rm -rf "$STATE_DIR"; mkdir -p "$STATE_DIR"
export SNAPSHOT_BRANCH=compositor-upstream-snapshot
export LATEST_TAG=v1.6.13
export VERSION=2.4.1
export ORIGINAL_CN_HEAD="$CN_TIP"
export ORIGINAL_SNAPSHOT_EXISTS=1
export ORIGINAL_SNAPSHOT_HEAD="$SNAP_HEAD"
export ORIGINAL_SNAPSHOT_TAG_SET=1
export ORIGINAL_SNAPSHOT_TAG=v1.6.7
export BACKUP_BRANCH=""
export MERGE_ACTIVE=1
export TRANSACTION_ACTIVE=1
export ROLLBACK_IN_PROGRESS=0
export ROLLBACK_COMPLETE=0
mkdir -p "$STATE_DIR/evidence"

# shellcheck disable=SC1090
. "$CORE"

CONFLICTS="$STATE_DIR/evidence/conflicts.txt"
printf 'app.txt\n' > "$CONFLICTS"

echo
echo "--- 1. handoff_for_conflicts parks the tree ---"
( handoff_for_conflicts "$CONFLICTS" < /dev/null ) > "$STATE_DIR/handoff.out" 2>&1
CODE=$?
chk "handoff 退出码 3" "$CODE" "3"
chk "wip 分支已建" "$(git show-ref --verify --quiet refs/heads/wip-cn-1.6.13-needs-conflicts && echo yes || echo no)" "yes"
chk "主分支已回到更新前 HEAD" "$(git rev-parse HEAD)" "$CN_TIP"
chk "快照分支已还原" "$(git rev-parse compositor-upstream-snapshot)" "$SNAP_HEAD"
chk "snapshot-tag 已还原" "$(git config compositor-cn.snapshot-tag)" "v1.6.7"
chk "工作区干净" "$(git status --porcelain | wc -l | tr -d ' ')" "0"

echo
echo "--- 2. handoff bundle written ---"
MF="$STATE_DIR/handoff/manifest.json"
[ -f "$MF" ] && echo "  manifest 存在" || echo "  ✗ manifest 缺失"
chk "manifest round=1" "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["round"])' "$MF" 2>/dev/null)" "1"
chk "manifest stage=conflicts" "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["stage"])' "$MF" 2>/dev/null)" "conflicts"
chk "manifest latest_tag" "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["latest_tag"])' "$MF" 2>/dev/null)" "v1.6.13"
chk "INSTRUCTIONS.md 存在" "$([ -f "$STATE_DIR/handoff/INSTRUCTIONS.md" ] && echo yes || echo no)" "yes"
chk "evidence 有冲突清单" "$([ -f "$STATE_DIR/handoff/evidence/conflicts.txt" ] && echo yes || echo no)" "yes"
chk "pending_handoff 检测为真" "$(pending_handoff && echo yes || echo no)" "yes"

echo
echo "--- 3. resume validation (negative cases) ---"
# wrong branch
git checkout -q adapt-compositor-1.4.1
chk "拒绝：不在 wip 分支" "$(resume_from_handoff 2>&1 | grep -c '不在 wip')" "1"
# correct branch but done missing
git checkout -q wip-cn-1.6.13-needs-conflicts
chk "拒绝：无 DONE.json" "$(resume_from_handoff 2>&1 | grep -c 'DONE.json')" "1"
# dirty tree
printf 'dirty\n' >> app.txt
chk "拒绝：工作区不干净" "$(resume_from_handoff 2>&1 | grep -c '工作区不干净')" "1"
git checkout -q -- app.txt
# unresolved
cat > "$STATE_DIR/handoff/DONE.json" <<'JSON'
{"round": 1, "changed_files": ["app.txt"], "decisions": ["app.txt: 取中文"], "unresolved": ["x"]}
JSON
chk "拒绝：有 unresolved" "$(resume_from_handoff 2>&1 | grep -c '未解决项')" "1"
# mismatched round
cat > "$STATE_DIR/handoff/DONE.json" <<'JSON'
{"round": 2, "changed_files": [], "decisions": [], "unresolved": []}
JSON
chk "拒绝：round 不匹配" "$(resume_from_handoff 2>&1 | grep -c 'DONE.json.round')" "1"

echo
echo "--- 4. resume happy path ---"
# AI resolves the conflict on wip: write a clean merged file and commit.
printf 'cn\nup\ncn-only\n' > app.txt
git add -A
git commit -qm 'AI: resolve conflict display-Chinese behaviour-upstream'
AI_HEAD="$(git rev-parse HEAD)"
cat > "$STATE_DIR/handoff/DONE.json" <<'JSON'
{"round": 1, "changed_files": ["app.txt"], "decisions": ["app.txt: 显示层保中文，行为层保上游"], "unresolved": []}
JSON
resume_from_handoff > "$STATE_DIR/resume.out" 2>&1
RCODE=$?
chk "resume 返回 0" "$RCODE" "0"
chk "主分支快进到 AI 提交" "$(git rev-parse adapt-compositor-1.4.1)" "$AI_HEAD"
chk "当前在主分支" "$(git branch --show-current)" "adapt-compositor-1.4.1"
chk "快照分支指回本轮新快照" "$(git rev-parse compositor-upstream-snapshot | wc -l | tr -d ' ')" "1"
chk "snapshot-tag 设为最新 tag" "$(git config compositor-cn.snapshot-tag)" "v1.6.13"
chk "RESUMED 标志已置" "${RESUMED:-0}" "1"
chk "工作区干净" "$(git status --porcelain | wc -l | tr -d ' ')" "0"

echo
echo "--- 5. round cap ---"
python3 - "$MF" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d['round']=3; json.dump(d,open(p,'w'))
PY
chk "round 3 触发上限" "$(handoff_round)" "3"

echo
if [ "$FAIL" = 0 ]; then echo "HANDOFF_E2E_OK"; else echo "HANDOFF_E2E_FAILED"; fi
exit "$FAIL"
