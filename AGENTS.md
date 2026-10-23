# AGENTS.md — Compositor-CN

Compositor-CN 是 macOS 图像编辑器 [Compositor](https://github.com/robbietilton/Compositor) 的简体中文维护分支。本文件是给在此仓库工作的 AI 智能体的操作约定：在继承上游规则的基础上，叠加「中文本地化 + 独立分发」的额外约束。

## 开工前必读

本项目在进行**大的动作**（合并官方版本、改动构建或签名配置、改动本地化机制、替换正式版 App 等）或承接**大的需求**时，**必须先读完下面两份文档再动手**：

- **需求文档** —— `docs/Compositor-CN-requirements.md`（仓库内；需求、本地化规范、验收标准）
- **本文件 AGENTS.md** —— 操作约定、禁止事项、每轮适配清单

冲突时的优先级：**用户当次的明确指示 > 需求文档 > 本文件**。

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

- 完整测试须 0 失败；记录本轮通过数。**每轮官方合并都会增删用例，数字必须重新取，不可沿用上一轮**。已知基线：1.4.7 = 539，1.4.9 = 569，1.4.10 = 577，1.5.3 = 654，1.5.5 = 687，1.5.6 = 707（历史「452 项」是 1.3.7 的，早已作废）。
- 取数用 `xcrun xcresulttool get test-results summary --path <xcresult>`，以顶层 `totalTestCount` / `passedTests` 为准；同一份结果里 device 级的数字会偏大，不要用。
- 系统区域为 zh_CN，测试宿主解析 zh-Hans，任何新增本地化都会命中硬编码英文断言——**测试断言必须用 `localizedString()`，禁止硬编码英文**。
- 本机开着 Stage Manager：系统会把置前的浮动窗口限制在左边缘边距之外（本显示器为 x ≥ 221），**窗口坐标类测试不要把面板停在屏幕左边缘**；`NSApp.activate` 在 xcodebuild 下不可靠，别依赖它。文件通知类断言在全量负载下会晚到，等待窗口要留足余量。

## 本地化：四类泄漏必须全部清零

字符串审计永远不够，四类泄漏缺一不可漏：

1. **AppKit 裸字面量**：`NSMenuItem(title:)`、`toolTip`、`accessibilityDescription`、`labelWithString` 等不自动本地化 → 显式 `localizedString()`。
2. **运行时拼接**：如 `"\(w) × \(h) px"`，静态扫描看不到 → 改为 `String(format: localizedString("..."))` 格式串。
3. **词条缺失**：源码有、目录没有 → 补 `Localizable.xcstrings`。
4. **SF Symbol 语言变体**：系统按 bundle 语言替换字形（`textformat` →「格式」）。文字类界面禁用字母类符号；文字图层徽标用 `NativeLayerList.textLayerIcon`（自行绘制字母 T）。

规则：

- **`Text(String)` 不本地化**：`Text(某 String 变量)` 走的是 verbatim 初始化器，`Text("字面量")` 才查表。凡是拼好的 `String`（汇总行、进度行、`LocalizedError.errorDescription`——`localizedDescription` 原样返回它）都必须自己 `String(format: localizedString(...))`。
- **`02-localization/audit_strings.py` 有三类盲区**，跑完它必须再补一轮扫描：① 枚举/变量承载的键（`Toggle(kind.titleKey)`、`LayerType.filterLabel`）；② 三元表达式（`isPlaying ? "Pause" : "Play"`）；③ AppKit setter（`field.placeholderString = "…"`）。判定「本地化完成」不能只看它的 0 缺口。
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

## 上游继承的约定（仍适用）

- 处理 `.comp` 项目文件：读 [docs/writing-comp-files.md](docs/writing-comp-files.md)。
- 项目文件格式：见 [docs/project-format.md](docs/project-format.md)；改动存档格式须同步 bump 格式版本号。
- 代码与注释用英文美式拼写（"color"）；**但 UI 字符串一律中文**（此条覆盖上游 AGENTS.md 的 "American spelling in UI"）。
- CI 在 push 时跑 CompositorTests。

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
3. 获取官方新标签源码并核对来源；若使用 tarball 合成快照，必须在提交与冲突记录中明确标注「非真实上游 tag commit」，并记录其父提交。
4. 逐文件合并官方新标签；冲突同时保留新版行为与中文定制；**并核对 Release 签名配置未被覆盖**。
5. 源码侧本地化审计四类泄漏清零 + 补齐词条与显示路径。
6. Debug + Release 构建；Release 启动冒烟测试；完整测试 0 失败。
7. 测试版人工验收（重点：新增菜单/提示/无障碍文本/条件状态，Camera RAW、PSD/PSB、导入导出）。
8. 通过可回滚流程替换正式版，核对版本 / build / Bundle ID / 签名 / 启动。
9. 提交、打 `vX.Y.Z-cn` 标签（标签语义 = 该周期最终状态，不是合并点），建立离机归档（git bundle + 含 .git 的 tar.gz），推送分支与发布标签。
10. **清理本轮产生的中间文件**（见「文件生命周期」的清理清单）。
11. **更新文档**（见「文档维护」）：测试基线、`docs/Compositor-CN-vX.Y.Z-conflict-resolution.md`、工作区日志。

## 文件生命周期：清理、归档与保留

原则：**项目产生的文件要么有明确归属，要么及时清理，不允许无限堆积。**

### 归属（每类只有一处）

| 类别 | 位置 | 说明 |
|---|---|---|
| 代码仓库 | `~/Desktop/Compositor-CN` | 唯一可构建、可提交的地方 |
| 备份与归档 | `~/Desktop/.Compositor-CN-Backups/` | **唯一主目录**；iCloud 同名目录是它的镜像 |
| 离机归档 | `~/Library/Mobile Documents/com~apple~CloudDocs/Compositor-CN-Backups/` | 与主目录保持一致 |
| 更新器历史版本 | `~/Desktop/.Compositor-CN-Backups/Updater-历史版本/` | 只存档，不安装 |
| 工作区（留档与证据） | `~/Desktop/AI/DSH/Compositor CN/` | 文档、审计脚本、核查证据；**不是 git 仓库** |
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

- 本文件的**唯一权威位置是仓库内 `AGENTS.md`**；工作区 `~/Desktop/AI/DSH/Compositor CN/AGENTS.md` 只是镜像，改完必须同步，避免两份漂移。
- 上游也有 `AGENTS.md`，**每轮合并可能冲突**：解决时保留本文件的中文版全部内容，同时吸收上游新增的通用工程约定。
- `README.md` 是**上游文件**（英文、介绍官方版），跟随上游合并，**不本地化、不改写**。
- 每轮适配结束必须更新：
  1. 本文件的测试通过数基线；
  2. `docs/Compositor-CN-vX.Y.Z-conflict-resolution.md` —— 记录该轮每个冲突的取舍（已有 1.2.9 / 1.3.3 / 1.3.7 / 1.4.7 / 1.4.9 / 1.4.10 / 1.5.3 / 1.5.5 / 1.5.6；**每轮都要写，别再断**）；
  3. 工作区 `.workbuddy-ai/memory/` 的当日日志与 `MEMORY.md`。
- 一次性的核查报告、交接文档留在工作区，不进仓库；结论过时要在文件里标注日期与「已过时」，不要默默留着误导后续。

## 关键文件

- `Compositor/Localizable.xcstrings` —— String Catalog（zh-Hans 词条）
- `Compositor/Localization.swift` —— `localizedString()` / `localizedHistoryAction()`
- `Compositor/CompositorApp.swift` —— 应用入口与动态菜单
- `Compositor/ContentView.swift` —— 工具栏与底部提示
- `Compositor/UI/NativeLayerList.swift` —— 图层面板、`textLayerIcon`、`sizeLabel`
- `Compositor/UI/KeyboardShortcuts.swift` —— 快捷键编辑器（显示层本地化）
- `Compositor.xcodeproj/project.pbxproj` —— 版本号 / Bundle ID / 签名配置
- `docs/writing-comp-files.md`、`docs/project-format.md` —— 上游文件格式约定
