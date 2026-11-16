#!/bin/bash
# Behavioural rehearsal for the audit_keys updater gate.
#
# The stage-0 static assertions cannot catch control-flow bugs under
# `set -Eeuo pipefail` + ERR trap. This fixture runs the real gate pattern:
# a key gap makes audit_keys.py exit 1, and the run must reach handoff
# (exit 3) rather than firing ERR trap / rollback (exit 99).
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
# SRC_DIR can be overridden to verify the deployed bundle after install.
SRC_DIR="${UPDATER_SRC_DIR:-$REPO_ROOT/tools/updater/src}"
ROOT="/tmp/v24-audit-gate-rehearsal"
rm -rf "$ROOT"; mkdir -p "$ROOT"; cd "$ROOT" || exit 1

FAIL=0
chk() {
    if [ "$2" = "$3" ]; then echo "  ✓ $1"; else echo "  ✗ $1（期望 [$3]，实际 [$2]）"; FAIL=1; fi
}

echo "=== audit_keys gate behavioural rehearsal ==="

# A minimal repo with a catalog that lacks "Text" and one key-carrier use.
cat > audit_keys.py <<'PY'
#!/usr/bin/env python3
import sys
# Emit the same gap report shape as the real audit_keys.py, then exit 1.
print("=== audit ===", flush=True)
print("--- LocalizedStringKey-carried literals NOT in catalog ---", flush=True)
print('  "Text"', flush=True)
sys.exit(1)
PY
chmod +x audit_keys.py
cat > catalog.json <<'JSON'
{}
JSON

# Build gate.sh from the REAL snippet in update.command, not a copy that can
# drift. The snippet is the lines between AUDIT_KEYS_SCRIPT and the closing
# `fi`; we wrap it with the same errexit + ERR trap environment that
# UpdaterCore.sh installs, and stub handoff_for_localization.
python3 - "$SRC_DIR/update.command" > "$ROOT/real-gate-body.sh" <<'PY'
import sys
from pathlib import Path
s = Path(sys.argv[1]).read_text()
start = s.index('    KEYS_REPORT="$STATE_DIR/audit-keys-gaps.txt"')
end = s.index('\nfi\n', s.index('handoff_for_localization', start))
body = s[start:end]
# Adapt the updater's variables to this fixture's locals.
body = body.replace('"$STATE_DIR/', '"$STATE/')
body = body.replace('"$REPO/tools/localization/audit_keys.py"', '"$AUDIT_KEYS_SCRIPT"')
body = body.replace('COMPOSITOR_CN_REPO="$REPO" ', '')
# The real body writes handoff reports; keep those, but drop its comment-only
# lines that reference missing context.
print(body)
PY

{
cat <<'SH'
#!/bin/bash
set -Eeuo pipefail
trap 'echo ERR_TRAP_FIRED; exit 99' ERR
handoff_for_localization() {
    echo "HANDOFF_CALLED:$1" >> "$STATE/gate-trace.txt"
    exit 3
}
STATE="$1"
AUDIT_KEYS_SCRIPT="$2"
SH
cat "$ROOT/real-gate-body.sh"
} > gate.sh
chmod +x gate.sh
mkdir -p state
bash gate.sh "$ROOT/state" "$ROOT/audit_keys.py" > "$ROOT/gate.out" 2>&1
CODE=$?

echo "  gate exit = $CODE"
grep -q ERR_TRAP_FIRED "$ROOT/gate.out" && TRAPPED=yes || TRAPPED=no
chk "未触发 ERR trap" "$TRAPPED" "no"
chk "退出码是 handoff 的 3" "$CODE" "3"
chk "走到了 handoff" "$(grep -c HANDOFF_CALLED "$ROOT/state/gate-trace.txt" 2>/dev/null || echo 0)" "1"
chk "写下了缺口报告" "$([ -s "$ROOT/state/audit-keys-gaps.txt" ] && echo yes || echo no)" "yes"

# Negative control: prove the old bare-python form WOULD have fired the trap.
cat > gate_old.sh <<'SH'
#!/bin/bash
set -Eeuo pipefail
trap 'echo ERR_TRAP_FIRED; exit 99' ERR
python3 "$1" > /dev/null 2>&1
KEYS_RESULT=$?
echo "SHOULD_NOT_REACH"
SH
chmod +x gate_old.sh
bash gate_old.sh "$ROOT/audit_keys.py" > "$ROOT/gate-old.out" 2>&1
OLD_CODE=$?
chk "旧写法确实触发 trap（反证）" "$(grep -c ERR_TRAP_FIRED "$ROOT/gate-old.out")" "1"
chk "旧写法退出 99（反证）" "$OLD_CODE" "99"

echo
if [ "$FAIL" = 0 ]; then echo "AUDIT_GATE_REHEARSAL_OK"; else echo "AUDIT_GATE_REHEARSAL_FAILED"; fi
exit "$FAIL"
