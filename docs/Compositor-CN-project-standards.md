# Compositor-CN 项目规范

> 版本 1.0 ｜ 2026-10-31 ｜ 依据 v1.5.12 基线整理
> 本文是**工程实践标准**：分支与标签、提交、代码、本地化编码、测试、构建发布、文档与文件管理。
> 「要做什么」看 `Compositor-CN-requirements.md`，「每轮按什么顺序做」看仓库根目录 `AGENTS.md`。

## 0 文档定位

### 0.1 三份文档的分工

| 文档 | 回答的问题 | 位置 |
| --- | --- | --- |
| `Compositor-CN-requirements.md` | 这个项目**要交付什么**（功能、非功能、验收标准、术语） | `docs/` |
| `AGENTS.md` | **每轮适配按什么顺序做**、踩过哪些坑、禁止事项 | 仓库根目录 |
| 本文件 | **写代码、写提交、发版本时遵守什么标准** | `docs/` |

### 0.2 优先级

用户当次的明确指示 > 需求文档 > `AGENTS.md` > 本文件。

本文件不与前两者冲突；若发现冲突，以前两者为准并**修正本文件**，不要各写一套。

### 0.3 规范用语

| 用语 | 含义 |
| --- | --- |
| **必须** / **禁止** | 硬性要求，违反即视为不合格，不得以「这次特殊」为由跳过 |
| **应当** | 默认遵守；偏离时必须在提交信息或冲突记录里写明理由 |
| **可以** | 允许的做法，不是要求 |

### 0.4 适用范围

适用于 `~/Desktop/Compositor-CN` 仓库内的一切改动，以及工作区 `~/Desktop/AI/DSH/Compositor CN` 内的文档、脚本、证据留档。

---

## 1 分支、版本与标签

### 1.1 分支

| 分支 | 用途 | 规则 |
| --- | --- | --- |
| `adapt-compositor-1.4.1` | **唯一长期分支**，所有工作在此提交 | 名字是历史遗留，**不代表版本**；版本一律看 `MARKETING_VERSION` |
| `compositor-upstream-snapshot` | 官方源码快照，合并的第二个父提交来源 | 只由 tarball 合成，**禁止**在此分支手工改代码 |
| `backup-cn-<版本>-merge-<sha>` | 合并前恢复点 | 每轮建一个，保留即可，不推远端 |
| `backup-cn-v2-<时间戳>` | 更新器自动建的事务恢复点 | 与既有恢复点重复，可以删 |
| `wip-cn-<版本>-needs-localization` | 更新器本地化门禁拦下时的暂存分支 | 只由更新器创建，处理完即可删 |

- **禁止**在长期分支之外新开功能分支做适配；本项目不是多人协作模式。
- 远端：`origin` = `ERVINYU18/Compositor`（自己的 fork），`upstream` = `robbietilton/Compositor`（官方）。
- 推送是纯快进，**禁止** `push --force`（标签同样禁止强推，见 1.3）。

### 1.2 版本号

| 字段 | 规则 |
| --- | --- |
| `MARKETING_VERSION` | **必须**等于本轮合入的官方版本号（如 `1.5.12`），不额外加后缀 |
| `CURRENT_PROJECT_VERSION` | **必须**等于官方的 build 号（如 `58`），不自增 |
| `CFBundleIdentifier`（App target） | **必须**恒为 `com.wonderassembly.compositor.cn`；合并后必须复验，上游 pbxproj 每次都带自己的 ID |
| tests / uitests target 的 Bundle ID | 跟随上游（`…compositor.tests` / `…uitests`），不必改成 `.cn` |

### 1.3 标签

- 发布标签格式：`vX.Y.Z-cn`，**必须**是 annotated tag（`git tag -a`）。
- 标签语义 = **该周期的最终状态**（功能 + 发布文档齐备的那个提交），**不是合并提交点**。合并点另有 `backup-cn-<版本>-merge-<sha>`。
- **禁止移动已推送的标签。** 打过标签之后只做纯文档修正（措辞、操作手册）时，不要重打标签——那个提交算下一周期的第一个提交。移动标签 = 强推 + 重建 bundle/tar.gz + 重跑 CI，改一句话就滚一轮。
- 更新器的「已是最新」判定依赖 `git config compositor-cn.snapshot-tag`，**每轮合并后必须**把它设成本轮的官方标签（如 `v1.5.12`），并确认快照分支是 HEAD 的祖先。

### 1.4 项目文件格式版本

`ProjectManifest.current`（`Compositor/IO/ProjectStore.swift`）只在**存档结构真的变了**时 bump。判断方法固定：

1. 看新字段所属类型**是否 `Codable`**、是否进入 `FilterLayerSettings` / 图层 / 文档结构。
2. 类型不是 Codable（只是 `Equatable, Sendable`，仅存在于运行时状态）→ **不 bump**。例：`RimLightSettings`（1.5.12），格式仍是 20。
3. 类型参与存档 → 字段改名/新增**必须** bump 版本，或写 `decodeIfPresent` + 默认值。例：`LensEffectSettings`（1.5.9 起 Codable）。
4. bump 后**必须**验证上一版存的项目仍能打开，并在冲突记录里写明「旧文件为什么能读」。

---

## 2 提交规范

### 2.1 语言与格式

- 提交信息用**英文**（与上游对照、`git log` 可读性）。专有名词、中文菜单名可以原样出现。
- 标题行 ≤ 72 字符，祈使句，不以句号结尾。
- 正文解释 **why**，不复述 diff。涉及取舍的，写清「取了哪边、为什么」。

### 2.2 三类提交的固定写法

**（a）官方源码快照**——由 tarball 合成，必须自带免责说明：

```
Official Compositor v1.5.12 source snapshot (GitHub tag v1.5.12 = <真实 sha>,
tarball via codeload; NOT the real upstream tag commit — parent is the
v1.5.11 snapshot <sha>).
```

**（b）合并提交**——正文必须覆盖五项：

1. 官方版本 + 快照 sha + 真实 tag sha；跳版本时写明「本轮含 vX.Y.Z」。
2. 本轮改动的范围与要点（新增功能、格式版本变化）。
3. 冲突清单：每个文件取了哪边、为什么。**禁止**只写「已解决冲突」。
4. 本地化增减：词条数从多少到多少，删除的键是什么。
5. 顺手修的既有问题（若有），单独一段。

**（c）文档提交**——`docs:` 或 `docs(<范围>):` 前缀，一行说清改了哪份文档的什么结论。

### 2.3 粒度与禁止事项

- 一个逻辑变更一个提交；合并提交与文档提交**分开**。
- **禁止** `git commit --amend` 已推送的提交；**禁止** `--no-verify` 跳过钩子。
- **禁止**在一个提交里混入无关的格式化、重命名。
- 提交前 `git status` 必须干净收尾：不留 `<<<<<<<` 标记、不留临时脚本。

---

## 3 代码规范

### 3.1 通用

- 跟随上游 Swift 风格；**代码与注释用英文**（美式拼写，`color` 而非 `colour`），**UI 字符串一律中文**。
- 不引入 SwiftLint / SwiftFormat 之类的新工具链——本项目只做本地化与分发，减少与上游的差异面。
- 改动范围**最小化**：能改一行不改两行，能不动上游文件就不动。差异越大，下轮合并越贵。

### 3.2 命名

| 对象 | 规则 |
| --- | --- |
| 类型 | `PascalCase`，与上游同名概念保持一致 |
| 成员 / 函数 | `camelCase`；布尔用 `is` / `has` / `can` 开头 |
| 文件 | 一个主类型一个文件，文件名 = 类型名（`RimLight.swift` 装 `RimLight` + `RimLightSettings` + `RimLighting`） |
| 本地化键 | 见 4.4 |
| 撤销步骤名 | 用 `localizedString(...)` 或 `localizedName`，**禁止**拼英文动词 + rawValue |

### 3.3 注释

- 注释解释**为什么**、边界条件、与上游的差异原因；不复述代码。
- 与本地化有关的特殊写法（为什么用 `verbatim`、为什么拆两个键）**必须**留一行注释，否则下轮合并的人会「顺手改回去」。
- 公开类型与关键算法保留文档注释（`///`），与上游风格一致。

### 3.4 文件与目录

- 新增文件放对目录：文档模型 `Document/`、渲染 `Rendering/`、界面 `UI/`、读写 `IO/`、测试 `CompositorTests/`。
- Xcode 16 的文件夹同步组（`PBXFileSystemSynchronizedRootGroup`）已生效：**新增文件不需要改 `project.pbxproj`**。手工往 pbxproj 里加 `PBXBuildFile` 属于错误操作。
- **禁止**把构建产物（`.xcresult`、DerivedData、`.app`）提交进仓库；`.gitignore` 已覆盖常见项。

### 3.5 并发与性能

- 新类型默认 `nonisolated` + `Sendable`，与上游一致；跨 actor 的状态改 `@MainActor`。
- 16 位路径：纯 Core Image / Metal 能一次跑完的滤镜，加进 `FilterKind.runsAtSixteenBits`；需要逐通道混合的加进 `mixesChannels`。判断错会静默降级成慢路径。
- GPU kernel 的 Swift 侧 `makeFunction(name:)` 与 Metal 源码里的函数名**必须**逐字对齐，改一侧就要改另一侧。
- 新增滤镜要在 `FilterSheet` 里给出全部滑杆的 `.help(...)` 说明——上游习惯如此，中文版照做。

### 3.6 禁止改动

- **禁止**恢复官方 Sparkle 入口：`updater.start()` / `checkForUpdates()` 不得出现，`Config/Info.plist` 不得有 `SUFeedURL`。
- **禁止**改 `README.md` 的内容（上游文件，跟随合并）。
- **禁止**改 App target 的签名四要素（见 6.2）。
- **禁止**为了「看起来更中文」去改 Codable 存储值、ColorSync 配置名、快捷键 `title` 等**数据用名**（见 4.5）。

---

## 4 本地化编码规范

### 4.1 三条上屏通道，三种写法

| 通道 | 触发条件 | 写法 |
| --- | --- | --- |
| `LocalizedStringKey` | `Text("字面量")`、`Button("字面量")`、`.help("字面量")`、`Label("字面量", …)` | 直接用字面量，SwiftUI 自动查表 |
| 显式查表 | 变量、拼好的 `String`、AppKit API、`LocalizedError.errorDescription` | `localizedString(...)` 包起来 |
| 原样输出 | 已本地化过的值、字母 T、格式名 | `Text(verbatim:)` |

**最容易踩的坑**：`Text(某 String 变量)`、`Button(某 String)`、`Picker(某 String, …)`、`Menu(某 String)`、`.accessibilityLabel(某 String)` **都不查表**——只有字面量才走 `LocalizedStringKey` 重载。静态审计查不出这类，只能人工过调用点。

### 4.2 枚举与集合

- 枚举值上屏**必须**用 `Text(verbatim: $0.localizedName)`；`localizedName` 由 `Localization.swift` 的通用扩展提供（`RawRepresentable where RawValue == String`）。
- 两套枚举共享同一个 rawValue 时**必须**各开命名空间（`Align …` / `Distribute …`），**禁止** `localizedString("Align " + rawValue)`——审计脚本会把 `"Align "` 当成缺词条的键。
- 菜单、`NSMenuItem`、`toolTip`、`accessibilityDescription` 这类 AppKit 路径**必须**显式 `localizedString()`。

### 4.3 格式串

- 用 `%@`（字符串）、`%lld`（整数）、`%.0f`（数值）等标准说明符；多占位符用位置说明符 `%1$lld × %2$lld`。
- **禁止**在 `localizedString(...)` 里做字符串插值：`localizedString("Color Picker (Light \(i))")` 每盏灯生成一个新键，永远翻译不到。改成 `String(format: localizedString("Color Picker (Light %lld)"), Int64(i))`。
- 拼好的行（汇总、进度、错误描述）**必须**自己 `String(format:)`，不能指望上层本地化。

### 4.4 词条键命名

| 场景 | 规则 | 示例 |
| --- | --- | --- |
| 普通界面文案 | 用**完整英文原句**，与上游 `LocalizedStringKey` 一致 | `Finding the subject…` |
| 命令面板 | 完整复合串 `Tool › X` / `Layer › …`，**禁止**裸名 | `Tool › Type` |
| 枚举撞键 | 前缀命名空间 | `Align Left Edges` / `Distribute Left Edges` |
| 同词不同义 | 加限定词，不复用 | `Round Cap`（线端）vs `Round`（形状） |

### 4.5 数据用名不译

以下**禁止**翻译，翻了会静默破坏功能：

- ColorSync 配置文件名字（`Generic CMYK Profile` 等，被 `CMYK.generic` 精确匹配）。
- Codable 存储值：`GIFDelayMode` 的 rawValue 之类。
- `ShortcutDefinition.title`（UserDefaults 键依赖它）——只在显示层 `localizedString(title)`。
- `LayerType`、`FilterKind` 等枚举的 rawValue 本身。
- 字体加载用的 PostScript name（显示用 `NSFont.displayName`）。
- 字母 **T**（文字工具标识），永远保持 `T`。

### 4.6 新增词条流程

1. 复制 `02-localization/add_<上一版>_keys.py` 为新版本脚本，改 `TRANSLATIONS`。
2. 脚本必须保留三道保护：备份到 `backups/`、**写入前验证「重新序列化 == 原字节」**（目录文件末尾无换行）、拒绝在含冲突标记时运行。
3. 废弃键走 `OBSOLETE` + `still_referenced()` 双重检查：源码里还有引用就不删。
4. 跑完**必须**再跑 `audit_strings.py`，并把「0 缺口」当起点而不是终点（见 4.7）。
5. docstring 里记录：本轮加了什么、删了什么、**哪些看着像字符串但确认不翻**及理由。

### 4.7 审计盲区与人工补扫

`audit_strings.py` 有三类盲区，报 0 缺口后**必须**人工补一轮：

| 盲区 | 查法 |
| --- | --- |
| `control("Choke", …)` 这类单词标题（行内无 `Text(`/`.help(`） | 列出本轮新增的 `control(` 调用逐个核 |
| 枚举/变量承载的键（`Toggle(kind.titleKey)`） | 过 `Text(`/`Button(`/`Picker(`/`Menu(` 后面跟变量的调用点 |
| 三元表达式（`isPlaying ? "Pause" : "Play"`） | 同上 |
| AppKit setter（`field.placeholderString = "…"`） | `grep` 赋值语句 |

另外两条可靠信号，**不得**当成误报：更新器的动态英文清单（`~/Library/Application Support/Compositor-CN-Updater/DynamicEnglish.txt`）和真实 UI 检查。

---

## 5 测试规范

### 5.1 命令

```bash
xcodebuild -project Compositor.xcodeproj -scheme Compositor -configuration Debug \
  -destination 'platform=macOS,arch=arm64' \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" test
```

签名覆盖三件套**必须**带上，否则报 "No signing certificate"——那是环境问题，不是代码问题。

### 5.2 断言

- **禁止**硬编码英文断言。系统区域 zh_CN、测试宿主解析 zh-Hans，任何新增本地化都会让英文断言失败。**必须**用 `localizedString(...)` 取期望值。
- 断言文案时优先断行为（状态、数值、像素），少断界面字符串。

### 5.3 命名与结构

- 文件 `XxxTests.swift`，与受测类型同名；用 Swift Testing 的 `@Test` + `#expect`，不混入 XCTest。
- 测试名描述**行为**（`hdrBlurPreviewsMatchTheResult`），不写 `test1`。
- 参数化用 `@Test(arguments:)`，不要复制粘贴多个函数。

### 5.4 基线

- 每轮**必须**重取通过数，**禁止**沿用上一轮。取数用：
  `xcrun xcresulttool get test-results summary --path <xcresult>`，以顶层 `totalTestCount` / `passedTests` 为准（device 级数字偏大）。
- 已知基线：1.4.7=539、1.4.9=569、1.4.10=577、1.5.3=654、1.5.5=687、1.5.6=707、1.5.7=720、1.5.8=723、1.5.9=734、1.5.11=745、1.5.12=752。
- 新增测试后**必须**同步更新 `AGENTS.md` 的基线行。

### 5.5 稳定性约束

- 读 AppKit 控件几何（`knobRect` / `trackRect`）**必须**先等布局：强制布局 + 轮询 + `travel > 0` 守卫。用固定 `sleep` 会拿到退化矩形，假失败甚至假通过。
- 窗口坐标类测试不要把面板停在屏幕左边缘（Stage Manager 会挪动它）。
- 文件通知类断言在全量负载下会晚到，等待窗口留足余量。
- **禁止**靠重跑掩盖偶发失败；先定位时序假设再改。

---

## 6 构建与发布

### 6.1 构建

- Release 构建**必须**零参数可用（配置正确时不需要任何签名覆盖）。
- 正式版**必须**用 Release 配置，**禁止**用 Debug 充当正式版。

### 6.2 签名四要素（App target，Debug 与 Release 都要）

```
CODE_SIGN_IDENTITY     = "-"
CODE_SIGN_STYLE        = Manual
DEVELOPMENT_TEAM       = ""
ENABLE_HARDENED_RUNTIME = NO
```

- **禁止**改回 Automatic，**禁止**打开 Hardened Runtime：library validation 会因内嵌 Sparkle 无 Team ID 在启动时 SIGABRT，**有开发者证书也一样**。
- 每次合并官方快照后**必须**复验这四处——上游 pbxproj 每次都会带自己的签名配置进来。
- `DEVELOPMENT_TEAM = 3E4X3B9Z9T` 出现在 tests / uitests target 属既有基线，不必改。

### 6.3 冒烟

- 替换正式版之前，产物**必须**做启动冒烟：`open` 后进程存活 ≥ 5 秒，并用 `sample` 确认主线程在 `ReceiveNextEventCommon` 之类的事件循环里（不是卡在锁或信号量）。
- 只看 `BUILD SUCCEEDED` 不算验证。

### 6.4 安装与回滚

1. 备份当前 `/Applications/Compositor-CN.app` 到 `~/Desktop/.Compositor-CN-Backups/pre-<新版本>-install-<时间戳>/`，并核对备份里的版本号。
2. 替换正式版，核对版本 / build / Bundle ID / 签名。
3. 装机版再冒烟一次。
4. **保留两级**安装回滚点，更早的清掉。

### 6.5 归档

- 一次归档 = 一个 `post-<版本>-cn-<时间戳>/`：`git bundle create --all`、含 `.git` 的 `tar.gz`（排除 `build-logs/`、`derived-data/`）、`SHA256SUMS.txt`、`STATE--<时间戳>.txt`。
- 桌面与 iCloud **各一份**，落地后各自 `shasum -c` 校验。
- **只保留最新一份归档**。删旧的之前**必须**用 `git bundle list-heads` 比对：新 bundle 的引用集合必须完整覆盖旧的（`comm -23` 输出为空）。
- 推送**必须**显式走代理，**单行**（`\` 续行后带空格会报 `parse error near '\n'`）：

```bash
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy git -c http.proxy=http://127.0.0.1:7897 push origin <分支或标签>
```

---

## 7 依赖与上游文件

- 不新增第三方依赖。内嵌 Sparkle 保持现状（存在、不启用）。
- `README.md`、`appcast.xml`、`docs/project-format.md`、`docs/writing-comp-files.md`、`docs/benchmarks/`、`docs/references/` 都是**上游文件**，跟随合并，不本地化、不改写。
- `docs/` 下以 `Compositor-CN-` 开头的文件才是本分支自己的文档。
- 上游 `AGENTS.md` 与本地同名文件冲突时：保留本地全部内容，吸收上游新增约定。

---

## 8 文档规范

### 8.1 权威位置

| 文档 | 权威位置 | 镜像 |
| --- | --- | --- |
| `AGENTS.md` | 仓库根目录 | 工作区同名文件（改完 `cp` 同步，`shasum -a 256` 验证一致） |
| 需求文档 | `docs/Compositor-CN-requirements.md` | 无 |
| 本规范 | `docs/Compositor-CN-project-standards.md` | 无 |
| 每轮冲突记录 | `docs/Compositor-CN-vX.Y.Z-conflict-resolution.md` | 无 |
| 交接文档 | 工作区 `Compositor-CN-项目交接文档-2026-10-16.md` | 无（文件名日期不代表内容版本） |

### 8.2 每轮必更新

1. `AGENTS.md`：测试基线、新增雷区、清单增补。
2. `docs/Compositor-CN-vX.Y.Z-conflict-resolution.md`：**每轮都要写**，不许断。
3. 交接文档：状态速查表、合并提交、归档与回滚点、风险。
4. 工作区当日日志 `.workbuddy-ai/memory/YYYY-MM-DD.md` 与长期记忆 `MEMORY.md`。

### 8.3 冲突记录模板

固定五段：官方源码来源（tag / sha256 / 合成快照说明）→ 上游改了什么 → 每个冲突的取舍 → 自动合并文件的抽查结果 → 本地化增减与验证结果。末尾附「人工验收重点」。

---

## 9 文件与目录规范

| 类别 | 位置 | 说明 |
| --- | --- | --- |
| 代码仓库 | `~/Desktop/Compositor-CN` | 唯一可构建、可提交的地方 |
| 备份与归档 | `~/Desktop/.Compositor-CN-Backups/` | 唯一主目录 |
| 离机归档 | `~/Library/Mobile Documents/com~apple~CloudDocs/Compositor-CN-Backups/` | 与主目录一致 |
| 更新器历史版本 | `~/Desktop/.Compositor-CN-Backups/Updater-历史版本/` | 只存档，不安装 |
| 工作区 | `~/Desktop/AI/DSH/Compositor CN/` | 文档、审计脚本、证据；**不是 git 仓库** |
| 构建中间产物 | Xcode DerivedData、工作区 `build-logs/` | 用完即清 |

- 删除**必须**走废纸篓（`/usr/bin/trash`），**禁止** `rm`。iCloud 内的文件用 `trash` 会报 NSCocoaErrorDomain 513，改 `mv` 到 `~/.Trash/`。
- **禁止清空废纸篓**：里面长期混着个人文件。只按名单逐项删本项目的东西。
- 删 `.xcresult` 之前先把摘要存到 `01-merge-scene-evidence/v1.5.x-test-summary-<日期>.txt`。
- 归档与回滚点之外，工作区**不保留**一次性分析产物（`audit-output-*.txt`、`*.json` 中间结果）。

---

## 10 放行门禁（Definition of Done）

一轮适配只有全部满足才允许打标签、装正式版。

| # | 门禁 | 判定 |
| --- | --- | --- |
| 1 | 冲突标记清零 | 全仓搜索 `<<<<<<<`、`=======`、`>>>>>>>` 均无命中 |
| 2 | 签名四要素 | App target Debug/Release 四处正确 |
| 3 | Sparkle 未复活 | `updater.start()` / `checkForUpdates()` / `SUFeedURL` 全无 |
| 4 | 版本号 | `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` 等于官方；Bundle ID 是 `.cn` |
| 5 | 构建 | Debug + Release 均成功 |
| 6 | 测试 | 全量 0 失败，本轮数字已重取并写入 `AGENTS.md` |
| 7 | 冒烟 | 产物与装机版各一次，存活 + 主线程空闲 |
| 8 | 本地化 | 审计 0 缺口 + 4.7 人工补扫 + 产物内 `zh-Hans.lproj` 抽查 |
| 9 | 归档 | bundle + tar.gz + STATE + SHA256SUMS，桌面与 iCloud 双份 `shasum -c` 通过，引用覆盖上一份 |
| 10 | 推送 | 分支与标签都在远端，`ls-remote` 与本地一致 |
| 11 | 文档 | 8.2 的四份全部更新 |

---

## 11 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 1.0 | 2026-10-31 | 首版。依据 v1.5.12 基线与 1.4.7→1.5.12 十二轮适配实践整理 |
