# AGENTS.md — Compositor-CN

Compositor-CN 是 macOS 图像编辑器 [Compositor](https://github.com/robbietilton/Compositor) 的简体中文维护分支。本文件是给在此仓库工作的 AI 智能体的操作约定：在继承上游规则的基础上，叠加「中文本地化 + 独立分发」的额外约束。

## 开工前必读

本项目在进行**大的动作**（合并官方版本、改动构建或签名配置、改动本地化机制、替换正式版 App 等）或承接**大的需求**时，**必须先读完下面三份文档再动手**：

- **需求文档** —— `docs/Compositor-CN-requirements.md`（仓库内；需求、本地化规范、验收标准）
- **项目规范** —— `docs/Compositor-CN-project-standards.md`（分支/标签、提交、代码、本地化编码、测试、构建发布的工程标准与放行门禁）
- **运行手册** —— `docs/Compositor-CN-runbook.md`（每轮要敲的命令：建快照、合并、补词条、借 Terminal 构建、装机、归档、推送、故障处置）
- **本文件 AGENTS.md** —— 操作约定、禁止事项、每轮适配清单

冲突时的优先级：**用户当次的明确指示 > 需求文档 > 本文件 > 项目规范**。运行手册只给命令，不定义规则。

## 沟通与文件安全（硬性要求）

沟通方式：

- 先给结论，再用通俗易懂的中文解释。
- 少用术语；必须使用时，紧接着说明它是什么意思、会带来什么影响。
- 不省略关键前提、风险和验证结果；严格区分「已修改」「已运行」「已验证成功」，不混为一谈。

文件安全：

- 不得擅自删除任何文件或目录；也不得用覆盖、清空、重置等方式变相删除内容。
- 只有用户明确要求删除、且删除目标与范围清楚时，才执行删除操作。
- 删除前先核对准确路径和影响范围；目标不清楚时，停止操作并向用户确认。
- 优先采用新增文件、局部修改、备份或可恢复的移动方式，而非删除。
- 完成后清楚说明改了什么；如确有删除，还要说明删除了什么、是否可恢复。

## 顶层原则

1. 这是「中文版」：所有用户可见界面必须是 zh-Hans，不能出现可见英文。
2. 功能一律跟随官方；本分支只做「本地化 + 独立分发」，不自行加减功能、不改变官方行为语义。
3. 每轮改动必须可构建、可测试、可人工验收、可回滚。

## 项目事实

- Bundle ID：`com.wonderassembly.compositor.cn`（与官方不同，避免冲突）
- 语言：zh-Hans
- 更新：独立的 Compositor-CN Updater；官方 Sparkle 更新入口被禁用（`startUpdater()` 永不调用）
- 本地化机制：`Compositor/Localizable.xcstrings`（SwiftUI 自动查表）+ `Compositor/Localization.swift` 的 `localizedString()`
- 项目格式：21（1.6.3 起；Reduce Noise 调整图层写入 `reduceNoise`，1–20 仍可读，旧版打不开 21）
- 版本以 `MARKETING_VERSION` 为准（不要看分支名——`adapt-compositor-1.4.1` 是历史遗留名，版本已前进）
- 官方上游：`upstream`（robbietilton/Compositor）；本地中文仓库：`origin`（ERVINYU18/Compositor，自己的 fork）

## 构建与测试

```bash
# 完整测试（必须带签名覆盖：本机无 CompositorTests 要求的 Mac Development 证书）
xcodebuild -project Compositor.xcodeproj -scheme Compositor -configuration Debug \
  -destination 'platform=macOS,arch=arm64' \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" test

# Release 构建（配置正确时应零参数可用，见「签名与发布」）
xcodebuild -project Compositor.xcodeproj -scheme Compositor -configuration Release \
  -destination 'platform=macOS,arch=arm64' build
```

- 完整测试须 0 失败；记录本轮通过数。**每轮官方合并都会增删用例，数字必须重新取，不可沿用上一轮**。已知基线：1.4.7 = 539，1.4.9 = 569，1.4.10 = 577，1.5.3 = 654，1.5.5 = 687，1.5.6 = 707，1.5.7 = 720，1.5.8 = 723，1.5.9 = 734，1.5.11 = 745，1.5.12 = 752，1.6.3 = 794，1.6.4 = 798，1.6.6 = 806，1.6.7 = 809，1.6.13 = 838，1.6.14 = 839（历史「452 项」是 1.3.7 的，早已作废）。
- **1.6.13 = 838 的来源**：由用户在真实终端跑 `构建验证装机-1.6.13.sh` 取得——`xcrun xcresulttool get test-results summary`（`build-logs/1.6.13-tests.xcresult`）顶层 `totalTestCount = 838`、`passedTests = 838`、`failedTests = 0`；device 级 962 是偏大值，不用。交叉核对 `CompositorTests/` 的 `@Test` 声明数也是 838。**原始产物已于 2026-11-18 清理（182 MB），摘要存工作区 `01-merge-scene-evidence/v1.6.13-test-summary-20261118.txt`；之后取数走 `tools/ci-test-count.py`。**
- **1.6.14 = 839 的来源**：Agent 会话内（完全访问模式）自己跑的全量测试取得——`build-logs/1.6.14-tests-run2.xcresult` 顶层 `totalTestCount = 839`、`passedTests = 839`、`failedTests = 0`；`tools/ci-test-count.py --declared` 与 `@Test` 声明数 839 一致。**首跑是 835/839**：`LayerRowDragTests` 4 项在全量并发下每个耗时 144 秒、合成鼠标事件没能拖动图层；该套件单独跑 6/6 全过（各约 3 秒），代码本轮未动，属全量负载下的时序抖动。全量失败时先单独重跑该套件再判断。
- **1.6.7 = 809 的来源（历史）**：本机跑不了全量测试，基线取自 CI run 43805717395 / 43805733435（`d7dfd82`，四个 job 全绿），并按「`@Test` 声明数」交叉核算。取数方式现已统一到 `tools/ci-test-count.py`。
- 取数用 `python3 tools/ci-test-count.py --declared <各批次.xcresult>`（多批次求和 + 与 `@Test` 声明核对；scoped run 跳过 filters 时加 `--exclude-suites`）。`summary` 顶层**不一定有** `totalTestCount`，没有时按 `passed + failed + skipped + expected` 相加；device 级数字会偏大（838 显示 962），不要用。
- 系统区域为 zh_CN，测试宿主解析 zh-Hans，任何新增本地化都会命中硬编码英文断言——**测试断言必须用 `localizedString()`，禁止硬编码英文**。
- 本机开着 Stage Manager：系统会把置前的浮动窗口限制在左边缘边距之外（本显示器为 x ≥ 221），**窗口坐标类测试不要把面板停在屏幕左边缘**；`NSApp.activate` 在 xcodebuild 下不可靠，别依赖它。文件通知类断言在全量负载下会晚到，等待窗口要留足余量。

### 在 Agent 会话里跑构建：先看会话有没有被沙箱包裹

**2026-11-20 更新（当前有效）**：DoubaoWork「完全访问」模式下，Agent 的命令直接在真实系统上执行，不再套 seatbelt，嵌套 `sandbox-exec` 恢复正常——已实测 Debug 构建 `BUILD SUCCEEDED`、单套件与全量 839 项测试全过。**判断方法**：先跑一句 `sandbox-exec -p '(version 1)(allow default)' /bin/echo ok`。返回 `ok` 就能直接构建/测试；返回 `sandbox_apply: Operation not permitted` 就是被套了沙箱，按下面的历史结论交回用户。

以下为历史记录（2026-10-27 / 2026-11-16，WorkBuddy 沙箱模式），**只对被沙箱包裹的会话成立，不要当成所有环境都这样**：

`xcodebuild` 在那种会话里跑不了：解析 SwiftPM 依赖时它自己会起 `sandbox-exec`，而外层已经是 seatbelt，于是固定失败 `sandbox-exec: sandbox_apply: Operation not permitted`。根因不是 SwiftPM，是**嵌套 `sandbox-exec` 整个不可用**——`sandbox-exec -p '(version 1)(allow default)' /bin/echo` 同样被拒。已实测**全部无效**的绕过手段，别再重复试：

- `dangerouslyDisableSandbox: true`（外层沙箱摘掉后仍失败，嵌套照样被拒）
- `-disableAutomaticPackageResolution`、`-onlyUsePackageVersionsFromResolvedFile`
- `-clonedSourcePackagesDirPath ~/Library/Caches/Compositor-CN-Build/SourcePackages`（复用已解析的 Sparkle 包）
- `SWIFTPM_DISABLE_SANDBOX=1`
- 复用已有 derivedDataPath（`~/Library/Caches/Compositor-CN-Build`）

**AppleScript 驱动 Terminal 这条路也已失效**（2026-11-16 实测）：`osascript -e 'tell application "Terminal" to do script ...'` → 权限违例 (-10004)；`tell application "System Events"` → 同样 -10004。`open -n -a Terminal` 本身返回 0，但拿不到窗口 id、也无法输入。

⇒ **被沙箱包裹时，唯一能跑 `xcodebuild` 的路径**：由用户在终端触发更新器 —— `update.command` 内部的 xcodebuild 不受那层沙箱约束。Agent 侧只能改代码、补词条、跑纯脚本审计、读 `xcresult`、推送、归档、写文档。**不被沙箱包裹时没有这个限制，构建、全量测试、启动冒烟都可以由 Agent 做。**

> 备注：`update.command` **只做 `build`，从不跑 test**。全量测试历来靠手工补，这一条别忘。

## 本地化：四类泄漏必须全部清零

字符串审计永远不够，四类泄漏缺一不可漏：

1. **AppKit 裸字面量**：`NSMenuItem(title:)`、`toolTip`、`accessibilityDescription`、`labelWithString` 等不自动本地化 → 显式 `localizedString()`。
2. **运行时拼接**：如 `"\(w) × \(h) px"`，静态扫描看不到 → 改为 `String(format: localizedString("..."))` 格式串。
3. **词条缺失**：源码有、目录没有 → 补 `Localizable.xcstrings`。
4. **SF Symbol 语言变体**：系统按 bundle 语言替换字形（`textformat` →「格式」）。文字类界面禁用字母类符号；文字图层徽标用 `NativeLayerList.textLayerIcon`（自行绘制字母 T），**工具栏文字工具用 `ToolRail.TextToolIcon`（`Text(verbatim: "T")`）**——2026-11-16 实测工具栏曾显示「格式」，`EditorSession.NavigationTool.symbol` 里的 `textformat` 是上游行为层不动，在 `ToolRail.toolButton` 显示层拦截。新增字母类图标后要跑 `audit_strings.py`，它把 `Text(verbatim:)` 列入「有意不翻译（复核）」，确认是 T 这类标识符即可。

规则：

- **`Text(String)` 不本地化**：`Text(某 String 变量)` 走的是 verbatim 初始化器，`Text("字面量")` 才查表。凡是拼好的 `String`（汇总行、进度行、`LocalizedError.errorDescription`——`localizedDescription` 原样返回它）都必须自己 `String(format: localizedString(...))`。
- **`tools/localization/audit_strings.py` 有三类盲区**，跑完它必须再补一轮扫描：① 枚举/变量承载的键（`Toggle(kind.titleKey)`、`LayerType.filterLabel`）；② 三元表达式（`isPlaying ? "Pause" : "Play"`）；③ AppKit setter（`field.placeholderString = "…"`）。判定「本地化完成」不能只看它的 0 缺口。
- **更新器的动态英文检测是可靠信号，别当成误报**：它扫出 `Text($0.rawValue)` 之类会把枚举 rawValue 直接上屏的写法，命中就整笔事务回滚（v1.5.7 就因此回滚）。清单在 `~/Library/Application Support/Compositor-CN-Updater/DynamicEnglish.txt`。修法照仓库惯例：`Text(verbatim: $0.localizedName)`，rawValue 保持英文只让目录供中文。
- 字母 **T** 是文字工具标识，永远保持 `T`，禁止翻成「格式」或任何中文。
- 字体菜单显示用 `NSFont.displayName`，内部加载/识别仍用 PostScript name。
- 格式化串用 `%@` / `%lld` 等标准说明符；多占位符可用位置说明符（`%1$lld × %2$lld`）。
- **数据用名不译**：ColorSync 配置文件名字（`Generic CMYK Profile` 等）被 `CMYK.generic` 按字符串精确匹配，翻译会静默破坏查找；`GIFDelayMode` 的 rawValue 之类 Codable 存储值同理。
- 术语必须统一（见 `docs/Compositor-CN-requirements.md` 的术语表）。
- 快捷键编辑器：`ShortcutDefinition.title` 是持久化的稳定英文 id（UserDefaults 键依赖它），**只在显示层 `localizedString(title)`，禁止改 `title` 本身**；搜索须同时匹配中英文。

## 签名与发布（踩过坑，务必遵守）

- 本机无开发者证书，只能 ad-hoc 签名。
- Release 配置必须是：`CODE_SIGN_IDENTITY = "-"`、`CODE_SIGN_STYLE = Manual`、`DEVELOPMENT_TEAM = ""`、`ENABLE_HARDENED_RUNTIME = NO`（见提交 `b6dae44`）。
- **严禁改回 Automatic 或打开 Hardened Runtime**：Hardened Runtime 的 library validation 会因内嵌 Sparkle 无 Team ID 而在启动时 SIGABRT，且即使有开发者证书也仍会失败。
- ⚠️ **每次合并官方快照都会把上游 pbxproj 带进来，极易覆盖上述 Release 修复**——合并后必须重新核对这两个配置是否还在。
- 替换正式版前必须对产物做启动冒烟测试（open 后进程存活 ≥5 秒），不要只看 BUILD SUCCEEDED。
- 安装必须可回滚：先备份旧 App 并校验，旧版保留至新版验收通过。
- ⚠️ **装机必须先移走旧 App 再 `ditto`，不能直接 `ditto` 覆盖**（2026-11-16 v1.6.7 实测）：`ditto` 对目录是「合并」语义，直接覆盖会把旧包里新包没有的文件（Debug 构建的 `Compositor.debug.dylib`、`__preview.dylib`）留下，破坏签名 seal。App 仍能启动（ad-hoc 签名不在启动时强制校验），但 `codesign -v --deep --strict` 会报 `a sealed resource is missing or invalid` / `file added: ...debug.dylib`。**装机后必须跑 `codesign -v --deep --strict` 并把通过作为完成条件**，不能只查版本号。正确顺序：`sudo mv /Applications/Compositor-CN.app /Applications/Compositor-CN.app.old-<时间戳>` → `sudo ditto <新包> /Applications/Compositor-CN.app` → strict 校验 → 启动冒烟。**这套流程 V2.4.0 更新器已全自动执行**（Release 构建 + 旧包归档 + strict 门禁 + 冒烟）；上面是应急手动兜底的步骤说明。

## 上游继承的约定（仍适用）

- 处理 `.comp` 项目文件：读 [docs/writing-comp-files.md](docs/writing-comp-files.md)。
- 项目文件格式：见 [docs/project-format.md](docs/project-format.md)；改动存档格式须同步 bump 格式版本号。
- 代码与注释用英文美式拼写（"color"）；**但 UI 字符串一律中文**（此条覆盖上游 AGENTS.md 的 "American spelling in UI"）。
- CI 在 push 时跑 `verify.yml`。**push 后要确认真的触发了**（`gh api repos/ERVINYU18/Compositor/actions/runs?per_page=3`）—— Actions 被关过两次，`actions/permissions` 在关闭时也显示 `enabled: true`，靠它判断不出来。关闭期间推的提交需 `gh workflow run verify.yml -R ERVINYU18/Compositor --ref <分支或标签>` 手动补。
- **四个 job**：`unit`（CompositorTests 分 first / rest / windows / filters 四批，各批一个 `.xcresult`）、`release-build`（Release 构建 + 产物无 `*.debug.dylib` / `__preview.dylib` + `codesign -v --deep --strict`）、`localization-leak`（zh-Hans 启动扫界面英文，`CompositorUITests/LocalizationLeakTests.swift`）、`screenshots`（强制 `-AppleLanguages (zh-Hans)` 截图，与上一次成功 run 的 PNG 做像素 diff，artifact 为 informational 不阻断）。
- **`localization-leak` 会因菜单抖动假红**（2026-11-20 实测）：它逐个菜单项扫，扫到某个索引时菜单被系统关掉，就会报 `Failed to get matching snapshot: No matches found for Descendants matching type MenuItem` 并判红——这是查询失败，不是扫出了英文。先看日志有没有真正的「English」条目：没有就 `gh run rerun <run> --failed` 重跑，别改代码。
- **`unit` 的静态门禁**：`tools/localization/assert_text_tool_icon.py`（T 图标不变量，`233540f` 之前失败、之后通过）、`tools/localization/test-leak-rules.py`（泄漏规则 24 个 fixture）、`audit_strings.py` + `audit_keys.py`。
- **测试数核对**：`tools/ci-test-count.py` 对多批次 `.xcresult` 求和（**用顶层计数：`summary` 不一定有 `totalTestCount`，没有时按 `passed+failed+skipped+expected`；device 级数字会重复计数**）并与 `@Test` 声明数核对。filters 批次被 scope 跳过时 `scripts/ci-tests.sh` 传 `--exclude-suites`，否则 747 vs 838 必然误报（`5190d99` 修）。
- **FILTERS 范围**：workflow 按 diff 决定要不要跑 filters 批次（Camera Raw / Hue-Saturation / Levels / 各 Filter 套件）；改动 `Compositor.xcodeproj/`、`verify.yml`、`scripts/ci-tests.sh` 会让它全量跑一遍。

## 更新器（Compositor-CN Updater）

**位置与版本**：`/Applications/Compositor-CN Updater.app`，当前 **V2.4.1 / 241**（2026-11-18 装入并短路冒烟通过）。主逻辑在 `Contents/Resources/UpdaterCore.sh`，入口 `update.command`。**权威源码在仓库 `tools/updater/src/`，app bundle 是部署副本；改更新器必须同步两处并提交**，否则工作区脏会被更新器的干净门禁挡下（+V2.4.0 首装就踩过）。完整记录见工作区 `更新器V2.4实施记录.md`。

- **判「已是最新」四要素**：已装 App 版本 == 官方最新 tag、`snapshot-tag` == 最新 tag、快照分支存在、**且是 HEAD 祖先**。手工合并完必须补查后两条，否则更新器会重跑整个合并。
- **本地化门禁是 `handoff_for_localization` 不是回滚**：命中「新增动态英文 / 缺 zh-Hans / 键承载缺口」时提交到 `wip-cn-<版本>-needs-localization`、仓库回到干净状态、正式版不动、退出码 3。有未解决冲突时仍回滚，绝不提交冲突标记。
- ⚠️ **errexit 陷阱（V2.4.0 踩过并修）**：`update.command` 是 `set -Eeuo pipefail`，`UpdaterCore.sh` 装了 ERR trap → `on_unexpected_error` 回滚。门禁里跑会返回非 0 的脚本**必须吸收退出码**：`KEYS_RESULT=0; python3 ... || KEYS_RESULT=$?`。直接取 `$?` 会先触发 ERR trap 回滚整笔合并，handoff 根本到不了。**静态断言证明不了控制流**，这类修法必须有行为级 fixture（见 `tools/updater/test-audit-keys-gate.sh`，它提取真实代码跑，带旧写法反证）。
- **V2.4.0 已修**：装机即删旧 App（改为归档留两级回滚点）、无 strict 校验（加 `codesign -v --deep --strict`，诊断落 `STATE_DIR/codesign-strict.log`）、装 Debug 包（改 Release）、签名四要素被冲掉（自动恢复含错误 identity 归一化）、`APP_PATCH_FAILED` 硬中止（改 `*_DRIFT` 留痕）。**新增 `audit_keys.py` 门禁**覆盖 `LocalizedStringKey` switch 与三元承载的键（`Text` 键曾漏四轮）。
- **✅ V2.4.1 首次真实实跑（2026-11-20，1.6.13 → 1.6.14，无冲突）**：Release 构建成功并装的是 Release 包（`Contents/MacOS/` 只有 `Compositor`，无 debug dylib）；`pre-1.6.14-install-20261120-172108` 旧包归档已产出；`codesign-strict.log` 为空（strict 通过）；`audit-keys.log` 报 0 个键承载缺口，`DynamicEnglish.txt` / `MissingTranslations.txt` / `patch-drift.txt` 均为空；无冲突所以没走 handoff。**但这一轮没有新建备份分支**——回滚点是合并前的提交 `43b3d62`（origin 上也有）。下一轮仍要盯 handoff 分支路径，它还没被真实冲突验证过。`last-conflicts.txt` 不会被清空，看到旧内容不代表本轮有冲突，以时间戳为准。
- **改更新器**：备份到 `Updater-历史版本/` → 改仓库 `tools/updater/src/` 两脚本 → `bash -n` → 跑 `tools/updater/` 的**五个**演练（parks-merge / refuses-conflict / stage0-safety / audit-keys-gate / handoff-resume-e2e）→ 同步部署到 app bundle + bump 两处版本号（`VERSION` 与 `Info.plist`）+ 重签 → 在「已是最新」状态跑短路冒烟。演练支持 `UPDATER_CORE=` / `UPDATER_SRC_DIR=` 指向部署副本验证。命令见运行手册第 10 节。
- **版本 bump 要改两处**：`update.command` 的 `VERSION` 和 applet `Info.plist` 的 `CFBundleShortVersionString` / `CFBundleVersion`，漏一处「关于」里版本对不上。
- ⚠️ **V2.3 Dev 不要装**：是另一个工具（`--rehearse` 默认、`/private/tmp` 隔离、遇内容冲突直接 fail、从不安装、目标硬编码 v1.4.7、**无 CN 补丁**），装上去功能倒退。

## 更新器交接协议（V2.4.1，用户说「继续更新」时执行）

更新器遇到白名单外的冲突、或补丁/本地化门禁时，不再丢弃合并结果，而是把带冲突标记（如需）的合并树停在 `wip-cn-<版本>-needs-*` 分支，并在 `~/Library/Application Support/Compositor-CN-Updater/handoff/` 写交接包。用户到会话里说「继续更新」，按下面做：

1. **读交接包**：`manifest.json`（`round`/`stage`/`wip_branch`/`latest_tag`/各 HEAD/backup）、`INSTRUCTIONS.md`（与本协议一致）、`evidence/`（门禁报告、冲突清单、`upstream-changes.diff` 上游完整 diff、`audit.json`）。
2. **切到 wip 分支**：`cd <仓库> && git checkout <wip_branch>`。该分支含完整合并结果；`stage=conflicts` 时文件里**保留 `<<<<<<<` 标记**，那是要你解的，不是损坏。
3. **逐文件取舍**：按本文档「本地化」与「签名与发布」的规则——**显示层保留中文，行为层保留上游**。禁止「全部 ours / 全部 theirs」或整文件覆盖。上游新增 UI 若用裸 `.help("literal")` / `.accessibilityLabel("literal")`，那在本项目走 `LocalizedStringKey` 自动查表，是既定惯例，**不要**改成 `localizedString()`；只有参数已是 `String`（三元结果、拼接、变量）时才显式包装。
4. **补词条**：照 `docs/Compositor-CN-requirements.md` 术语表，用 `tools/localization/add_<版本>_keys.py` 模板（备份 + 字节级序列化守卫 + 追加不覆盖）。
5. **自查**：跑 `audit_strings.py` + `audit_keys.py`，再人工扫三类盲区（枚举/变量承载的键、三元表达式、AppKit setter）；SF Symbol 字母类符号按文档规则处理（T 保持 T）。
6. **提交 + 写回**：在 wip 分支提交（写清每个冲突取了哪边、为什么），起草本轮冲突记录草稿放工作区，然后写 `handoff/DONE.json`：
   ```json
   {"round": <与 manifest 一致>, "changed_files": ["..."], "decisions": ["文件: 取哪边/为什么"], "unresolved": []}
   ```
   `unresolved` 非空如实写，交用户判断。
7. **交还**：告诉用户「回更新器按回车续跑」。**你不构建、不推送、不装机、不打标签**——更新器会重跑门禁、恢复状态、快进主分支，再走构建装机，成功后归档交接包（wip 分支保留复核）。

轮次上限 3：门禁连续不过时更新器给编号菜单（重试 / 中止回滚 / 保留现场转人工），不会无限循环。

## 禁止事项

- 不恢复官方 Sparkle 更新入口。
- 不用「全部 ours / 全部 theirs」或整文件覆盖处理合并冲突。
- 不绕过动态英文与真实 UI 检查，只凭目录缺失数判定本地化完成。
- 不在未保存现场/未确认恢复点时执行 reset --hard、merge --abort、强制切分支或清理备份。
- 不在脏工作区或未确认状态时启动正式 Compositor-CN Updater。
- 不用 `rm` 删除任何项目文件（走废纸篓，见「文件生命周期」）；不在仓库或工作区长期堆放构建产物（`.xcresult`、DerivedData）。

## 每轮适配清单

1. 只读复核：分支 / HEAD / 无 MERGE_HEAD / 工作区干净 / snapshot-tag。
2. 干净基线上建立恢复点（备份分支或离机归档）。
3. 获取官方新标签源码并核对来源；若使用 tarball 合成快照，必须在提交与冲突记录中明确标注「非真实上游 tag commit」，并记录其父提交。**更新器可能一次跳过好几个版本**（2026-10-27 就从 1.5.9 直接到 1.5.11），合并前先用 `git ls-remote --tags upstream` 确认中间版本号，被跳过的改动会一起压进这一轮 —— 提交信息与冲突记录里要写明「本轮含 vX.Y.Z」。
4. 逐文件合并官方新标签；冲突同时保留新版行为与中文定制；**并核对 Release 签名配置未被覆盖**。
5. 源码侧本地化审计四类泄漏清零 + 补齐词条与显示路径。
6. Debug + Release 构建；Release 启动冒烟测试；完整测试 0 失败。
7. 测试版人工验收（重点：新增菜单/提示/无障碍文本/条件状态，Camera RAW、PSD/PSB、导入导出）。
8. 通过可回滚流程替换正式版，核对版本 / build / Bundle ID / 签名 / 启动。
9. 提交、打 `vX.Y.Z-cn` 标签（标签语义 = 该周期最终状态，不是合并点），建立离机归档（git bundle + 含 .git 的 tar.gz），推送分支与发布标签。**标签打过之后只做纯文档修正（操作手册、措辞）时不要再移动标签** —— 那个提交算下一周期的第一个提交，标签留在「功能 + 发布文档」齐备的那个点上；否则每改一句文档就要强推标签、重建归档、重跑 CI，越滚越乱。**推送必须显式指定 Clash 代理**，否则 git 走直连（本机 `github.com` 直连不通，会 75 秒超时；沙箱注入的代理会 502）。**写成单行，别用 `\` 续行** —— 复制粘贴时 `\` 后容易带空格，zsh 会报 `parse error near '\n'`：
   ```bash
   env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy git -c http.proxy=http://127.0.0.1:7897 push origin <分支或标签>
   ```
10. **清理本轮产生的中间文件**（见「文件生命周期」的清理清单）。
11. **更新文档**（见「文档维护」）：测试基线、`docs/Compositor-CN-vX.Y.Z-conflict-resolution.md`、工作区日志。

## 文件生命周期：清理、归档与保留

原则：**项目产生的文件要么有明确归属，要么及时清理，不允许无限堆积。**

### 归属（每类只有一处）

| 类别 | 位置 | 说明 |
|---|---|---|
| 代码仓库 | `~/Desktop/AI/AI Project/Compositor CN/Compositor-CN` | 唯一可构建、可提交的地方 |
| 备份与归档 | `~/Desktop/AI/AI Project/Compositor CN/.Compositor-CN-Backups/` | **唯一主目录**；iCloud 同名目录是它的镜像 |
| 离机归档 | `~/Library/Mobile Documents/com~apple~CloudDocs/Compositor-CN-Backups/` | 与主目录保持一致 |
| 更新器历史版本 | `~/Desktop/AI/AI Project/Compositor CN/.Compositor-CN-Backups/Updater-历史版本/` | 只存档，不安装 |
| 工作区（留档与证据） | `~/Desktop/AI/AI Project/Compositor CN/` | 交接文档、核查证据、历史留档；**不是 git 仓库** |
| 本地化与更新器脚本 | 仓库内 `tools/localization/`、`tools/updater/` | 随仓库走，换机器不用重建 |
| 构建中间产物 | Xcode DerivedData、工作区 `build-logs/` | 用完即清 |

⚠️ `~/Documents/.Compositor-CN-Backups/` 已于 2026-10-12 废弃并删除，**不要再往那里放东西**。

### 归档约定

- 一次归档 = 一个 `post-<版本>-cn-<时间戳>/` 子目录，内含：`git bundle create --all` 的 `.bundle`、含 `.git` 的整仓库 `.tar.gz`、`SHA256SUMS.txt`、`STATE--<时间戳>.txt`（记录 HEAD / 父提交 / 版本 / 测试结果 / 恢复命令）。
- 桌面与 iCloud **各存一份**，落地后各自 `shasum -c` 校验。
- 同一版本只保留「最终状态」那一份；中间快照（`-inprogress-`）和重复的 `post-` 目录在下轮开始前清掉。
- 删旧归档前先验证 `git bundle list-heads` 对比：旧 bundle 的引用必须被新 bundle 完全覆盖，否则会丢引用。

### 每轮结束后的清理清单

1. 工作区 `build-logs/` 里本轮之前的 `.xcresult`（单个可达数百 MB）→ 清；`.log` 只有几 MB，可留作证据。
2. `~/Library/Developer/Xcode/DerivedData/Compositor-*` → 可清（下次构建自动重建）。**只删本项目那个目录**，别动共享缓存和其它项目。
3. 旧 App 回滚点（`pre-*-install-*`）：新版验收通过后可逐步清，**至少保留最近两级**。
4. `~/Library/Application Support/Compositor-CN-Updater/` 下的旧日志与空审计产物 → 可清。
5. 合并中途快照（`-inprogress-`、更新器回滚留下的临时目录）→ 该轮完成后即清。

### 删除方式（硬性）

- **禁止 `rm`**：一律走废纸篓（`trash`），保证可恢复。
- iCloud Drive 内的文件用 `trash` 会报权限错误（NSCocoaErrorDomain 513），改用 `mv <文件> ~/.Trash/<新名字>`。
- 涉及个人目录时，删除前必须列出完整路径与影响范围并经用户确认；小批量（≤10 项）执行，每批完成后复核。

### 定期维护节奏

- **每轮适配结束**：走一遍上面的清理清单 + 更新文档。
- **每月**：核对桌面与 iCloud 归档是否一致（文件列表 + `shasum -c`）；清一次 DerivedData 与旧 `.xcresult`。
- **每次准备用更新器前**：确认 `compositor-cn.snapshot-tag` == 官方最新 tag、且 `compositor-upstream-snapshot` 分支存在**并且是 HEAD 的祖先**——缺一条更新器就不会短路，会把整个合并流程重跑一遍。手工合并完一轮后尤其要补查后两条。

## 文档维护

- 本文件的**唯一权威位置是仓库内 `AGENTS.md`**；工作区 `~/Desktop/AI/AI Project/Compositor CN/AGENTS.md` 只是镜像，改完必须同步，避免两份漂移。
- 上游也有 `AGENTS.md`，**每轮合并可能冲突**：解决时保留本文件的中文版全部内容，同时吸收上游新增的通用工程约定。
- `README.md` 是**上游文件**（英文、介绍官方版），跟随上游合并，**不本地化、不改写**。
- 每轮适配结束必须更新：
  1. 本文件的测试通过数基线；
  2. `docs/Compositor-CN-vX.Y.Z-conflict-resolution.md` —— 记录该轮每个冲突的取舍（已有 1.2.9 / 1.3.3 / 1.3.7 / 1.4.7 / 1.4.9 / 1.4.10 / 1.5.3 / 1.5.5 / 1.5.6 / 1.5.7 / 1.5.8 / 1.5.9 / 1.5.11 / 1.5.12；**每轮都要写，别再断**）；
  3. 工作区 `.workbuddy-ai/memory/` 的当日日志与 `MEMORY.md`。
- `docs/Compositor-CN-runbook.md` 不按轮更新，但**命令变了就要改**（换了工具链、换了代理端口、更新器改了流程）。它是给下一个接手的人照抄的，写错了比没写更糟。
- 一次性的核查报告、交接文档留在工作区，不进仓库；结论过时要在文件里标注日期与「已过时」，不要默默留着误导后续。**换 agent / 换机器时，工作区必须一并移交**，否则丢的是交接文档、历史决策与全部证据（脚本已在仓库 `tools/`，不受影响）。见运行手册第 12 节。

## 关键文件

- `Compositor/Localizable.xcstrings` —— String Catalog（zh-Hans 词条）
- `Compositor/Localization.swift` —— `localizedString()` / `localizedHistoryAction()`
- `Compositor/CompositorApp.swift` —— 应用入口与动态菜单
- `Compositor/ContentView.swift` —— 工具栏与底部提示
- `Compositor/UI/NativeLayerList.swift` —— 图层面板、`textLayerIcon`、`sizeLabel`
- `Compositor/UI/KeyboardShortcuts.swift` —— 快捷键编辑器（显示层本地化）
- `Compositor.xcodeproj/project.pbxproj` —— 版本号 / Bundle ID / 签名配置
- `docs/writing-comp-files.md`、`docs/project-format.md` —— 上游文件格式约定
- `docs/Compositor-CN-runbook.md` —— 每轮的命令集（含更新器运维与故障处置）
- `tools/localization/` —— 补词条与审计脚本（`audit_strings.py`、`add_<版本>_keys.py`）
- `tools/updater/` —— 更新器回归演练（改更新器前后必跑）
