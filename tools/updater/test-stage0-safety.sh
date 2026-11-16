#!/bin/bash
# Stage 0 safety-guard rehearsal for V2.4.0.
#
# Read-only source assertions plus pure-Python checks. No sudo, no real app,
# no transaction execution — those need the real updater process and are
# reserved for the user's "already up to date" smoke test after install.
#
# Covers the five V2.2.1 safety defects:
#   1. signing four-element restoration (App target Debug + Release)
#   2. tests/uitests team IDs left untouched
#   3. codesign --deep --strict gate present in install_app_transaction
#   4. previous app kept as a rollback point (no unconditional delete)
#   5. Release (not Debug) build configuration and product path
#   6. patch-drift trace instead of a misleading APP_PATCH_FAILED
#
# Usage:
#   bash tools/updater/test-stage0-safety.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
# SRC_DIR can be overridden to verify the deployed bundle after install:
#   UPDATER_SRC_DIR="/Applications/Compositor-CN Updater.app/Contents/Resources" \
#     bash tools/updater/test-stage0-safety.sh
SRC_DIR="${UPDATER_SRC_DIR:-$REPO_ROOT/tools/updater/src}"
ROOT="/tmp/v24-stage0-rehearsal"
rm -rf "$ROOT"; mkdir -p "$ROOT"

FAIL=0
chk() {
    if [ "$2" = "$3" ]; then echo "  ✓ $1"; else echo "  ✗ $1（期望 [$3]，实际 [$2]）"; FAIL=1; fi
}

echo "=== Stage 0 safety rehearsal ==="

# ------------------------------------------------------------------
# 1-2. Signing patch: verify the real block inside update.command works
#      on a pbxproj clobbered the way upstream clobbers it.
# ------------------------------------------------------------------
echo
echo "--- signing patch (real code extracted from update.command) ---"
mkdir -p "$ROOT/sign/Compositor.xcodeproj"
cp "$REPO_ROOT/Compositor.xcodeproj/project.pbxproj" "$ROOT/sign/Compositor.xcodeproj/"

python3 - "$SRC_DIR/update.command" "$ROOT/sign/Compositor.xcodeproj/project.pbxproj" <<'PY'
import re, sys
from pathlib import Path

script = Path(sys.argv[1]).read_text()
p = Path(sys.argv[2])
s = p.read_text()

# Clobber signing the way upstream does. Release loses the identity key;
# Debug carries a wrong identity — both must be normalized to "-".
ids = ['8F311FBB304F03BC0017D14F', '8F311FBC304F03BC0017D14F']
for i, bid in enumerate(ids):
    start = s.find(bid + ' /*'); end = s.find('\n\t\t};', start)
    b = s[start:end]
    if i == 0:
        # Debug: wrong identity present (upstream Automatic style).
        b = re.sub(r'CODE_SIGN_IDENTITY = [^;]*;',
                   'CODE_SIGN_IDENTITY = "Apple Development";', b)
    else:
        # Release: identity key absent.
        b = b.replace('CODE_SIGN_IDENTITY = "-";\n\t\t\t\t', '')
    b = re.sub(r'CODE_SIGN_STYLE = [^;]+;', 'CODE_SIGN_STYLE = Automatic;', b)
    b = re.sub(r'DEVELOPMENT_TEAM = [^;]*;', 'DEVELOPMENT_TEAM = 3E4X3B9Z9T;', b)
    b = re.sub(r'ENABLE_HARDENED_RUNTIME = [^;]+;', 'ENABLE_HARDENED_RUNTIME = YES;', b)
    s = s[:start] + b + s[end:]
p.write_text(s)

# Extract the real signing block from update.command and execute it.
start_marker = "# V2.4.0: restore the App target's ad-hoc signing settings."
start = script.index(start_marker)
end = script.index("\np.write_text(s)", start)
block = script[start:end]
# The block is indented for the enclosing Python heredoc; strip one level.
block = "\n".join(line[1:] if line.startswith(" ") else line
                  for line in block.splitlines())
ns = {"s": p.read_text(), "re": re}
exec(compile(block, "<extracted-signing-patch>", "exec"), ns)
p.write_text(ns["s"])
PY

python3 - "$ROOT/sign/Compositor.xcodeproj/project.pbxproj" > "$ROOT/signing-state.txt" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
for bid in ['8F311FBB304F03BC0017D14F', '8F311FBC304F03BC0017D14F']:
    start = s.find(bid + ' /*'); end = s.find('\n\t\t};', start); b = s[start:end]
    v = [re.search(k + r' = "?([^;"]*)"?;', b) for k in
         ['CODE_SIGN_IDENTITY','CODE_SIGN_STYLE','DEVELOPMENT_TEAM','ENABLE_HARDENED_RUNTIME']]
    print('|'.join(m.group(1) if m else '(none)' for m in v))
PY
chk "App-Debug 四要素" "$(sed -n '1p' "$ROOT/signing-state.txt")" '-|Manual||NO'
chk "App-Release 四要素" "$(sed -n '2p' "$ROOT/signing-state.txt")" '-|Manual||NO'
chk "tests/uitests team ID 未改" "$(grep -c 'DEVELOPMENT_TEAM = 3E4X3B9Z9T' "$ROOT/sign/Compositor.xcodeproj/project.pbxproj")" "6"

# ------------------------------------------------------------------
# 3. strict seal gate: present, inside the transaction function, and
#    wired to fail (not just a warning).
# ------------------------------------------------------------------
echo
echo "--- strict seal gate ---"
chk "strict 校验存在" "$(grep -c 'codesign -v --deep --strict' "$SRC_DIR/UpdaterCore.sh")" "1"
# Confirm it sits inside install_app_transaction, before its closing brace.
chk "strict 门禁在事务内且会 fail" "$(python3 - "$SRC_DIR/UpdaterCore.sh" <<'PY'
import sys
s = open(sys.argv[1]).read()
start = s.index('install_app_transaction()')
end = s.index('\n# Localization gates', start)
body = s[start:end]
print('IN_TRANSACTION' if 'codesign -v --deep --strict' in body and 'fail "' in body.split('codesign -v --deep --strict')[1] else 'BAD')
PY
)" "IN_TRANSACTION"

# ------------------------------------------------------------------
# 4. Old app retained: no unconditional rm -rf of INSTALL_BACKUP.
# ------------------------------------------------------------------
echo
echo "--- old app retained ---"
chk "旧包归档提示存在" "$(grep -c '旧版已归档为回滚点' "$SRC_DIR/update.command")" "1"
chk "归档到项目备份目录" "$(grep -c '.Compositor-CN-Backups/pre-' "$SRC_DIR/update.command")" "1"
chk "不再删除 INSTALL_BACKUP" "$(grep -c 'rm -rf "$INSTALL_BACKUP"' "$SRC_DIR/update.command")" "0"

# ------------------------------------------------------------------
# 5. Release build configuration and product path.
# ------------------------------------------------------------------
echo
echo "--- Release build ---"
chk "构建配置是 Release" "$(grep -c -- '-configuration Release' "$SRC_DIR/update.command")" "1"
chk "构建配置不是 Debug" "$(grep -c -- '-configuration Debug' "$SRC_DIR/update.command")" "0"
chk "产物路径是 Release" "$(grep -c 'Build/Products/Release/Compositor.app' "$SRC_DIR/update.command")" "1"
chk "产物路径不是 Debug" "$(grep -c 'Build/Products/Debug/Compositor.app' "$SRC_DIR/update.command")" "0"

# ------------------------------------------------------------------
# 6. Patch-drift trace instead of a misleading generic error.
# ------------------------------------------------------------------
echo
echo "--- patch drift trace ---"
chk "drift 清单由补丁写入" "$(grep -c 'patch-drift.txt' "$SRC_DIR/update.command")" "5"
chk "drift 命中时写 last-conflicts" "$(grep -c 'cp "$STATE_DIR/patch-drift.txt" "$STATE_DIR/last-conflicts.txt"' "$SRC_DIR/update.command")" "1"
chk "不再硬报 APP_PATCH_FAILED:" "$(grep -c 'APP_PATCH_FAILED:' "$SRC_DIR/update.command")" "0"
chk "BLEND 补丁同构 drift 留痕" "$(grep -c 'BLEND_PATCH_DRIFT' "$SRC_DIR/update.command")" "2"
chk "不再硬报 BLEND_PATCH_FAILED:" "$(grep -c 'BLEND_PATCH_FAILED:' "$SRC_DIR/update.command")" "0"

# ------------------------------------------------------------------
# 7. audit_keys gate wired into the updater.
# ------------------------------------------------------------------
echo
echo "--- audit_keys gate ---"
chk "调用 audit_keys.py" "$(grep -c 'python3 "\$AUDIT_KEYS_SCRIPT"' "$SRC_DIR/update.command")" "1"
chk "缺口走 handoff" "$(python3 - "$SRC_DIR/update.command" <<'PY'
import sys
s = open(sys.argv[1]).read()
i = s.index('KEYS_RESULT=$?')
block = s[i:i+900]
print('WIRED' if 'handoff_for_localization' in block else 'NOT_WIRED')
PY
)" "WIRED"

# ------------------------------------------------------------------
# 8. strict gate keeps diagnostics.
# ------------------------------------------------------------------
echo
echo "--- strict diagnostics ---"
chk "诊断日志落 STATE_DIR" "$(grep -c 'codesign-strict.log' "$SRC_DIR/UpdaterCore.sh")" "1"
chk "strict 行不再吞 stderr" "$(grep -c 'codesign -v --deep --strict "\$APP" 2>/dev/null' "$SRC_DIR/UpdaterCore.sh")" "0"
chk "strict 输出重定向到日志" "$(grep -c 'codesign -v --deep --strict "\$APP" >"\$seal_log" 2>&1' "$SRC_DIR/UpdaterCore.sh")" "1"

# ------------------------------------------------------------------
# 9. audit_keys gate must absorb the exit status under ERR trap, and the
#    archive block must sit after the transaction commits.
#    (Behavioural control-flow is covered by test-audit-keys-gate.sh.)
# ------------------------------------------------------------------
echo
echo "--- gate control flow + archive safety ---"
chk "门禁吸收退出码（不触发 ERR trap）" "$(grep -c '|| KEYS_RESULT=\$?' "$SRC_DIR/update.command")" "1"
chk "归档块在事务提交之后" "$(python3 - "$SRC_DIR/update.command" <<'PY'
import sys
s = open(sys.argv[1]).read()
print('yes' if s.index('TRANSACTION_ACTIVE=0') < s.index('# V2.4.0: archive the old app') else 'no')
PY
)" "yes"
chk "归档 mkdir 有兜底" "$(grep -c 'if mkdir -p "\$BACKUP_DIR" 2>/dev/null' "$SRC_DIR/update.command")" "1"
chk "归档 chown 不中止" "$(grep -c 'sudo chown -R.*|| true' "$SRC_DIR/update.command")" "1"
chk "归档用 ROLLBACK_SOURCE" "$(grep -c 'ROLLBACK_SOURCE' "$SRC_DIR/update.command")" "6"

echo
if [ "$FAIL" = 0 ]; then echo "STAGE0_REHEARSAL_OK"; else echo "STAGE0_REHEARSAL_FAILED"; fi
exit "$FAIL"
