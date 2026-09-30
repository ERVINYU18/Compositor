# AGENTS.md — Compositor-CN

Compositor-CN 是 macOS 图像编辑器 [Compositor](https://github.com/robbietilton/Compositor) 的简体中文维护分支。本文件是给在此仓库工作的 AI 智能体的操作约定：在继承上游规则的基础上，叠加「中文本地化 + 独立分发」的额外约束。

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
- 官方上游：`upstream`（robbietilton/Compositor）；本地中文仓库：`origin`（Echo-Smith/Compositor）

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

- 完整测试须 0 失败；记录本轮通过数。历史「452 项」是 1.3.7 的数字，不可沿用。
- 系统区域为 zh_CN，测试宿主解析 zh-Hans，任何新增本地化都会命中硬编码英文断言——**测试断言必须用 `localizedString()`，禁止硬编码英文**。

## 本地化：四类泄漏必须全部清零

字符串审计永远不够，四类泄漏缺一不可漏：

1. **AppKit 裸字面量**：`NSMenuItem(title:)`、`toolTip`、`accessibilityDescription`、`labelWithString` 等不自动本地化 → 显式 `localizedString()`。
2. **运行时拼接**：如 `"\(w) × \(h) px"`，静态扫描看不到 → 改为 `String(format: localizedString("..."))` 格式串。
3. **词条缺失**：源码有、目录没有 → 补 `Localizable.xcstrings`。
4. **SF Symbol 语言变体**：系统按 bundle 语言替换字形（`textformat` →「格式」）。文字类界面禁用字母类符号；文字图层徽标用 `NativeLayerList.textLayerIcon`（自行绘制字母 T）。

规则：

- 字母 **T** 是文字工具标识，永远保持 `T`，禁止翻成「格式」或任何中文。
- 字体菜单显示用 `NSFont.displayName`，内部加载/识别仍用 PostScript name。
- 格式化串用 `%@` / `%lld` 等标准说明符；多占位符可用位置说明符（`%1$lld × %2$lld`）。
- 术语必须统一（见 `Compositor-CN-需求文档` 术语表）。
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

## 每轮适配清单

1. 只读复核：分支 / HEAD / 无 MERGE_HEAD / 工作区干净 / snapshot-tag。
2. 干净基线上建立恢复点（备份分支或离机归档）。
3. 逐文件合并官方新标签；冲突同时保留新版行为与中文定制；**并核对 Release 签名配置未被覆盖**。
4. 源码侧本地化审计四类泄漏清零 + 补齐词条与显示路径。
5. Debug + Release 构建；Release 启动冒烟测试；完整测试 0 失败。
6. 测试版人工验收（重点：新增菜单/提示/无障碍文本/条件状态，Camera RAW、PSD/PSB、导入导出）。
7. 通过可回滚流程替换正式版，核对版本 / build / Bundle ID / 签名 / 启动。
8. 提交后建立离机归档（git bundle + 含 .git 的 tar.gz）。

## 关键文件

- `Compositor/Localizable.xcstrings` —— String Catalog（zh-Hans 词条）
- `Compositor/Localization.swift` —— `localizedString()` / `localizedHistoryAction()`
- `Compositor/CompositorApp.swift` —— 应用入口与动态菜单
- `Compositor/ContentView.swift` —— 工具栏与底部提示
- `Compositor/UI/NativeLayerList.swift` —— 图层面板、`textLayerIcon`、`sizeLabel`
- `Compositor/UI/KeyboardShortcuts.swift` —— 快捷键编辑器（显示层本地化）
- `Compositor.xcodeproj/project.pbxproj` —— 版本号 / Bundle ID / 签名配置
- `docs/writing-comp-files.md`、`docs/project-format.md` —— 上游文件格式约定
