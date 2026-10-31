# Compositor-CN 运行手册

> 这是**可复制的命令集**。规则与「为什么」在 `AGENTS.md` 和 `Compositor-CN-project-standards.md`，
> 本文件只回答「具体敲什么」。
> 所有 `<版本>` 换成官方 tag 的版本号（如 `1.5.13`），`<快照sha>` 换成上一轮的快照提交。

---

## 0 开工前自查（只读，不改任何东西）

```bash
cd ~/Desktop/AI/DSH/Compositor CN/Compositor-CN
git status --short --branch
git log -1 --format='%H %s'
test -f .git/MERGE_HEAD && echo "⚠️ 有未完成的合并" || echo "无 MERGE_HEAD"
git config --get compositor-cn.snapshot-tag
git tag --list 'v1.*-cn' | sort -V | tail -3
/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" -c "Print :CFBundleVersion" /Applications/Compositor-CN.app/Contents/Info.plist
```

**判定「干净」**：工作区无改动、无 `MERGE_HEAD`、HEAD 与 origin 一致、已装 App 版本 = 最新标签的版本。
任一条不满足就先停下来查，不要往下走。

---

## 1 查官方新版本

```bash
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy git -c http.proxy=http://127.0.0.1:7897 ls-remote --tags upstream | tail -12
```

**必须**把「当前基线 → 最新」之间的所有版本号列出来。被跳过的版本会一起压进这一轮，
提交信息和冲突记录里要写明「本轮含 vX.Y.Z」。

---

## 2 下载官方源码，建合成快照

```bash
mkdir -p /tmp/cn-merge-<版本> && cd /tmp/cn-merge-<版本>
curl -sL --max-time 180 -o v<版本>.tar.gz https://codeload.github.com/robbietilton/Compositor/tar.gz/refs/tags/v<版本>
shasum -a 256 v<版本>.tar.gz          # 记下来，STATE 里要用
tar xzf v<版本>.tar.gz
grep -m2 -E "MARKETING_VERSION|CURRENT_PROJECT_VERSION" Compositor-<版本>/Compositor.xcodeproj/project.pbxproj
```

建快照（**父提交必须是上一个快照**，这样祖先链不断）：

```bash
cd ~/Desktop/AI/DSH/Compositor CN/Compositor-CN
export GIT_INDEX_FILE=/tmp/cn-merge-<版本>/snap.idx
rm -f "$GIT_INDEX_FILE"
git --work-tree=/tmp/cn-merge-<版本>/Compositor-<版本> add -A .
TREE=$(git write-tree)
COMMIT=$(git commit-tree "$TREE" -p <快照sha> -m "Official Compositor v<版本> source snapshot (GitHub tag v<版本> = <真实tag sha>, tarball via codeload; NOT the real upstream tag commit — parent is the v<上一版> snapshot <快照sha>).")
unset GIT_INDEX_FILE
git update-ref refs/heads/compositor-upstream-snapshot "$COMMIT"
git log --oneline -2 compositor-upstream-snapshot
```

提交信息里**必须**带「NOT the real upstream tag commit」——这是给未来的自己看的免责声明。

---

## 3 合并

```bash
cd ~/Desktop/AI/DSH/Compositor CN/Compositor-CN
git branch backup-cn-<版本>-merge-$(git rev-parse --short HEAD)
git merge --no-ff --no-commit <新快照sha>
grep -rn -E "^(<<<<<<<|=======|>>>>>>>)" Compositor CompositorTests CompositorUITests Compositor.xcodeproj
```

冲突处理原则：**显示层保留中文，行为层保留上游新版**。禁止「全部 ours / 全部 theirs」。

先看上游改了什么再动手：

```bash
git diff --stat <上一快照sha> <新快照sha>
git diff --name-status <上一快照sha> <新快照sha> | grep -E "^[ADR]"
```

---

## 4 合并后必查四项

```bash
# ① 签名四要素（App target 的 Debug 与 Release 都要）
grep -n -E "CODE_SIGN_IDENTITY|CODE_SIGN_STYLE|DEVELOPMENT_TEAM|ENABLE_HARDENED_RUNTIME" Compositor.xcodeproj/project.pbxproj

# ② Sparkle 是否复活
grep -rn -E "updater\.start\(\)|checkForUpdates\(\)|startUpdater\(\)|SUFeedURL" Compositor/ Config/ || echo "干净"

# ③ 上游删掉的符号是否还被我们引用（冲突标记里看不出来）
git diff <上一快照sha> <新快照sha> | grep -E "^-" | grep -oE "(func|var|let|struct|enum|class) [A-Za-z_][A-Za-z0-9_]*" | sort -u

# ④ 未冲突但被改的 UI 文件里，localizedString 有没有被冲掉
git diff HEAD -- Compositor/UI/ | grep -E "^-.*localizedString" || echo "没被冲掉"
```

---

## 5 本地化

脚本在仓库内 `tools/localization/`（随仓库走，换机器不用重建）：

```bash
cd ~/Desktop/AI/DSH/Compositor CN/Compositor-CN/tools/localization
cp add_<上一版>_keys.py add_<版本>_keys.py    # 改 TRANSLATIONS / OBSOLETE / docstring
python3 add_<版本>_keys.py
python3 audit_strings.py
```

脚本自带三道保护：备份到 `backups/`、写入前验证「重新序列化 == 原字节」、拒绝在含冲突标记时运行。
**不要绕过**——目录文件末尾没有换行，直接 `json.dump` 会把整文件重写。

`audit_strings.py` 报 0 缺口只是起点，还要人工补扫四类盲区（见项目规范 4.7）：

```bash
# 单词标题：control("Choke", …) 这类行内没有 Text( / .help(
grep -rn "control(\"" Compositor/UI/ | grep -vE "Text\(|\.help\("

# 变量上屏：Text( / Button( / Picker( / Menu( 后面跟的不是字面量
grep -rnE "\b(Text|Button|Picker|Menu|Label)\([a-zA-Z_$][a-zA-Z0-9_.$]*\)" Compositor/
```

---

## 6 构建与测试

`xcodebuild` 在 WorkBuddy 进程里跑不了（嵌套 `sandbox-exec` 被拒）。写成脚本交给真实 Terminal：

```bash
cat > /tmp/wb-run.sh <<'SH'
#!/bin/zsh
exec > /tmp/wb-run.log 2>&1
cd ~/Desktop/AI/DSH/Compositor CN/Compositor-CN || exit 1
echo "=== START $(date) ==="
xcodebuild -project Compositor.xcodeproj -scheme Compositor -configuration Release \
  -destination 'platform=macOS,arch=arm64' build 2>&1 | tail -20
echo "RELEASE_EXIT=$?"
xcodebuild -project Compositor.xcodeproj -scheme Compositor -configuration Debug \
  -destination 'platform=macOS,arch=arm64' \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" \
  -resultBundlePath "$HOME/Desktop/AI/DSH/Compositor CN/build-logs/<版本>-tests.xcresult" test 2>&1 | tail -25
echo "TEST_EXIT=$?"
echo "=== END $(date) ==="
SH
chmod +x /tmp/wb-run.sh
rm -f /tmp/wb-run.log
open -n -a Terminal          # 必须带 -n，否则只激活不建窗口
```

然后用 computer-use：`gui_list_windows` 取终端窗口 id → `create_task` 输入 `zsh /tmp/wb-run.sh` 回车。
shell 侧分段轮询（单个循环超过 600 秒会被 SIGTERM 打断，脚本不受影响，重起一轮即可）：

```bash
for i in $(seq 1 40); do grep -q "^TEST_EXIT=" /tmp/wb-run.log 2>/dev/null && break; /bin/sleep 12; done
grep -E "^(RELEASE_EXIT=|TEST_EXIT=|\*\* BUILD|\*\* TEST)" /tmp/wb-run.log
```

取测试数：

```bash
xcrun xcresulttool get test-results summary --path "$HOME/Desktop/AI/DSH/Compositor CN/build-logs/<版本>-tests.xcresult" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['totalTestCount'], d['passedTests'], d['failedTests'])"
```

---

## 7 装机（带回滚点）

```bash
# 备份当前正式版
STAMP=$(date +%Y%m%d-%H%M%S)
BK=~/Desktop/AI/DSH/Compositor CN/.Compositor-CN-Backups/pre-<版本>-install-$STAMP
mkdir -p "$BK"
ditto "/Applications/Compositor-CN.app" "$BK/Compositor-CN-<旧版本>.app"
/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$BK/Compositor-CN-<旧版本>.app/Contents/Info.plist"

# 替换
killall Compositor 2>/dev/null || true
NEW=$(ls -d ~/Library/Developer/Xcode/DerivedData/Compositor-*/Build/Products/Release/Compositor.app | head -1)
mv "/Applications/Compositor-CN.app" /tmp/Compositor-CN-<旧版本>-old.app
ditto "$NEW" "/Applications/Compositor-CN.app"

# 核对 + 冒烟
/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" -c "Print :CFBundleVersion" -c "Print :CFBundleIdentifier" "/Applications/Compositor-CN.app/Contents/Info.plist"
codesign -dv "/Applications/Compositor-CN.app" 2>&1 | grep -E "Identifier|Signature|TeamIdentifier"
open "/Applications/Compositor-CN.app"; /bin/sleep 7
PID=$(/usr/bin/lsappinfo info -only pid "com.wonderassembly.compositor.cn" | grep -oE '[0-9]+' | head -1)
/usr/bin/sample "$PID" 1 -file /tmp/smoke.txt >/dev/null 2>&1; grep -c "ReceiveNextEventCommon" /tmp/smoke.txt
```

---

## 8 标签、归档、推送

```bash
cd ~/Desktop/AI/DSH/Compositor CN/Compositor-CN
git add -A && git commit -F - <<'MSG'
docs: record the v<版本> merge and its <N>-test baseline
MSG

git tag -a v<版本>-cn -m "Compositor-CN <版本> (build <B>)

Official Compositor v<版本> merged on top of the <上一版> baseline.
Merge commit: <sha>. Upstream snapshot: <快照sha> (synthetic, parent <上一快照>) —
not the real upstream tag commit, which is <真实tag sha>.
Tests: <N>/<N> passed. Localization: <M> keys."
git config compositor-cn.snapshot-tag v<版本>
git merge-base --is-ancestor <快照sha> HEAD && echo "快照是 HEAD 祖先 ✅"
```

归档：

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
DIR=~/Desktop/AI/DSH/Compositor CN/.Compositor-CN-Backups/post-<版本>-cn-$STAMP
mkdir -p "$DIR"
git bundle create "$DIR/Compositor-CN-all-refs-$STAMP.bundle" --all
tar czf "$DIR/Compositor-CN-repo-full-$STAMP.tar.gz" --exclude=build-logs --exclude=derived-data --exclude=.DS_Store -C ~/Desktop Compositor-CN
# 写 STATE--$STAMP.txt（模板见下）
cd "$DIR" && shasum -a 256 * > SHA256SUMS.txt && shasum -c SHA256SUMS.txt
rsync -a "$DIR/" "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Compositor-CN-Backups/$(basename "$DIR")/"
cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Compositor-CN-Backups/$(basename "$DIR")" && shasum -c SHA256SUMS.txt
```

STATE 模板必含：归档时间戳 / 版本与 build / Bundle ID / 签名 / 已装 App / 测试数 / 词条数 /
HEAD / 分支 / 标签（含语义说明）/ 本周期提交列表 / 合并提交与两个父 / 官方 tag sha /
源码 sha256 与「合成快照」声明 / 本周期要点 / 回滚命令 / 人工验收重点。

推送（**单行**，`\` 续行后带空格会报 `parse error near '\n'`）：

```bash
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy git -c http.proxy=http://127.0.0.1:7897 push origin adapt-compositor-1.4.1
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy git -c http.proxy=http://127.0.0.1:7897 push origin v<版本>-cn
```

---

## 9 收尾

```bash
# 先留测试摘要，再删 200M 的 xcresult
xcrun xcresulttool get test-results summary --path "build-logs/<版本>-tests.xcresult" > /tmp/summary.json
# …把关键数字写进 01-merge-scene-evidence/v1.<版本>-test-summary-<日期>.txt
/usr/bin/trash "build-logs/<版本>-tests.xcresult"
/usr/bin/trash /tmp/Compositor-CN-<旧版本>-old.app
rm -rf /tmp/cn-merge-<版本> ~/Library/Developer/Xcode/DerivedData/Compositor-*
```

四份文档必须更新：`AGENTS.md` 基线、`docs/Compositor-CN-v<版本>-conflict-resolution.md`、
交接文档、工作区当日日志。

---

## 10 更新器（Compositor-CN Updater）

**位置**：`/Applications/Compositor-CN Updater.app`，当前 **V2.2.1 / 221**。
资源在 `Contents/Resources/`：`update.command`（入口）、`UpdaterCore.sh`（主逻辑）、`Scripts/`、`Tests/`。

**它做什么**：查 GitHub API 拿官方最新 tag → 下载 tarball → 建快照 → 合并 → 构建 → 测试 →
本地化审计 → 事务化安装。任一步失败整笔回滚，正式版不受影响。

**判「已是最新」的四要素**（缺一就会重跑整个合并）：

1. 已装 App 版本 == 官方最新 tag
2. `git config compositor-cn.snapshot-tag` == 官方最新 tag
3. `compositor-upstream-snapshot` 分支存在
4. 该分支是 HEAD 的祖先

**两道本地化门禁的行为**：命中「新增动态英文」或「词条缺 zh-Hans」时**不再回滚**，
而是提交到 `wip-cn-<版本>-needs-localization`、仓库回到更新前干净状态、正式版不动、退出码 3。
这叫 `handoff_for_localization`。有未解决冲突时仍退回回滚，绝不提交冲突标记。

### 已知缺陷：`APP_PATCH_FAILED`

`CompositorApp.swift` **一冲突就必报 `APP_PATCH_FAILED`**。原因：CN 补丁脚本对「被 git 标为冲突」
的该文件有一组「6 条中文规则必须已恢复」的校验，但校验跑在冲突解决**之前**，文件里还是
`<<<<<<<`，替换全部匹配不上，6 条全命中 → 中止。

两个后果：

- 这一轮必然白跑，得手工接手。
- 它**连 `last-conflicts.txt` 都不写**，文件里留着上一轮的旧内容 —— 别把旧内容当本轮冲突。

修法二选一：见 `<<<<<<<` 就跳过校验；或把校验挪到冲突解决之后。

### 改更新器的流程

```bash
cp -R "/Applications/Compositor-CN Updater.app" ~/Desktop/AI/DSH/Compositor CN/.Compositor-CN-Backups/Updater-历史版本/Compositor-CN\ Updater-<旧版本>.app
# 改 Contents/Resources/update.command 或 UpdaterCore.sh
bash -n "/Applications/Compositor-CN Updater.app/Contents/Resources/update.command"
bash -n "/Applications/Compositor-CN Updater.app/Contents/Resources/UpdaterCore.sh"
cd "/Users/yi/Desktop/AI/DSH/Compositor CN"
cd ~/Desktop/AI/DSH/Compositor CN/Compositor-CN
bash "tools/updater/test-handoff-parks-merge.sh"        # 期望 REHEARSAL_OK
bash "tools/updater/test-handoff-refuses-conflict.sh"   # 期望 REHEARSAL2_OK
codesign --force --deep --sign - "/Applications/Compositor-CN Updater.app"
```

最后在「已是最新」状态下跑一次真实短路冒烟（会在「当前已经包含官方最新版」处退出，不建事务）。

⚠️ **V2.3 Dev 不要装**：它是另一个工具（`--rehearse` 默认、`/private/tmp` 隔离、遇内容冲突直接 fail、
从不安装、目标硬编码 v1.4.7、**没有 CN 补丁**）。装上去功能倒退。

---

## 11 故障处置

| 症状 | 处理 |
| --- | --- |
| `sandbox-exec: sandbox_apply: Operation not permitted` | `xcodebuild` 不能在 WorkBuddy 进程里跑，走第 6 节 |
| `No signing certificate` | 测试命令漏了签名覆盖三件套 |
| `git push` 报 502 / `CONNECT tunnel failed` | 那是沙箱注入的代理，不是 Clash。用第 8 节的单行命令显式指定 7897 |
| `git push` 报 `Empty reply` 或 75 秒超时 | 直连 github.com 不通。同上，走 Clash |
| `zsh: parse error near '\n'` | 多行命令粘贴时 `\` 后带了空格。全部改单行 |
| 更新器报 `APP_PATCH_FAILED` | 见第 10 节，手工接手合并 |
| 更新器报 `HTTP 422: Actions has been disabled` | 与本项目无关，是 fork 的 Actions 被关，需在网页启用 |
| 测试数对不上 | 用 `xcresulttool` 顶层 `totalTestCount`，别用 device 级数字 |
| 界面出现英文 | 先跑审计，再按项目规范 4.7 补扫四类盲区 |
| 装了新版启动即崩 | 查 `ENABLE_HARDENED_RUNTIME` 是否被上游 pbxproj 覆盖 |

---

## 12 换 agent / 换机器时要移交什么

| 对象 | 位置 | 缺了会怎样 |
| --- | --- | --- |
| 代码仓库 | `~/Desktop/AI/DSH/Compositor CN/Compositor-CN` | 没法干活（本地化与更新器脚本已在 `tools/`，随仓库走） |
| 工作区 | `~/Desktop/AI/DSH/Compositor CN/` | 丢交接文档（当前状态、历史决策）、历史证据与项目记忆 |
| 备份主目录 | `~/Desktop/AI/DSH/Compositor CN/.Compositor-CN-Backups/` | 丢归档与两级安装回滚点 |
| iCloud 镜像 | `~/Library/Mobile Documents/com~apple~CloudDocs/Compositor-CN-Backups/` | 丢离机防灾 |
| 更新器 App | `/Applications/Compositor-CN Updater.app` | 下一轮只能全程手工 |
| 项目记忆 | 工作区 `.workbuddy-ai/memory/` | 丢「踩过什么坑」的来龙去脉 |

**本机环境前提**（换机器必须重建，否则很多结论不成立）：

- 无开发者证书 → 只能 ad-hoc 签名，签名四要素不能改。
- `github.com` 直连不通 → 推送必须走 Clash `127.0.0.1:7897`。
- 系统区域 zh_CN → 测试断言必须用 `localizedString()`。
- 开着 Stage Manager → 窗口坐标类测试不要把面板停在屏幕左边缘。
- `xcodebuild` 在 WorkBuddy 进程里跑不了 → 必须借真实 Terminal。
