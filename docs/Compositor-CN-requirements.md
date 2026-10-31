# Compositor-CN 需求文档

> Compositor 简体中文维护分支 · 需求规格说明
> 版本 1.0 ｜ 2026-09-30 ｜ 依据 v1.4.1 适配实践整理

## 0 文档信息

本文档定义 Compositor-CN（macOS 图像编辑器 Compositor 的简体中文维护分支）的功能与非功能需求，作为此后每一个官方版本适配、验收与发布环节的依据。

本文档只约束本分支的行为，不替代官方 Compositor 的说明文档。功能定义始终以官方版本为准，本分支只在「本地化与分发」层面施加额外要求。

| 项目 | 约定 |
| --- | --- |
| 源码仓库 | `/Users/yi/Desktop/AI/AI Project/Compositor CN/Compositor-CN` |
| Bundle ID | `com.wonderassembly.compositor.cn` |
| 目标语言 | zh-Hans（简体中文） |
| 交付形态 | 独立 .app，ad-hoc 签名，独立更新器 |
| 上游 | github.com/robbietilton/Compositor |
| 当前基线版本 | 1.5.12（build 58）—— 每轮适配后更新 |

## 1 背景与目标

官方 Compositor 为英文单语应用。中文用户需要一个与官方功能同步、界面完整中文化、且不与官方更新机制冲突的独立版本。

**项目目标（G）：**

- **G1 功能同步** —— 每个官方正式版本发布后，以独立适配分支合入，功能与官方一致。
- **G2 完整中文化** —— 所有用户可见界面元素（含提示、弹窗、无障碍标签、快捷键面板）以 zh-Hans 呈现，无可见英文。
- **G3 独立更新** —— 使用独立的 Compositor-CN Updater；禁用官方 Sparkle 更新入口，二者互不干扰。
- **G4 可维护、可验证、可回滚** —— 每轮适配都必须能构建、能测试、能人工验收、能安全回滚。

**非目标：** 不自行增加官方没有的功能；不改变官方行为语义（仅在本地化所必需处做最小改动）。

## 2 运行环境与交付形态

| 项 | 要求 |
| --- | --- |
| 平台 | macOS，最低系统版本跟随官方（当前 26.0） |
| 架构 | Apple Silicon（arm64） |
| 签名 | ad-hoc（CodeDirectory flags=0x2），不使用开发者证书、不公证 |
| Hardened Runtime | 关闭（见 NFR-2 与 §8.1） |
| 更新 | Compositor-CN Updater（V2.2 及以上） |
| 语言目录 | `Localizable.xcstrings`（SwiftUI 自动查表）+ `Localization.swift` 的 `localizedString()` |

## 3 功能性需求（FR）

| 编号 | 需求 | 验证方式 |
| --- | --- | --- |
| FR-1 | 所有用户可见界面元素以 zh-Hans 呈现，无可见英文 | 源码侧审计四类泄漏清零 + 人工验收 |
| FR-2 | `Localizable.xcstrings` 中所有可翻译键均具备 zh-Hans 词条 | 脚本统计缺失 zh-Hans = 0 |
| FR-3 | 运行时生成的字符串（rawValue、拼接、格式化标题）同样中文化 | 动态字符串扫描 + 人工操作 |
| FR-4 | 文字工具的字母 T 是工具标识，保持原样（`Text(verbatim:)`/自行绘制），不翻译 | 新建文字图层检查缩略图与工具栏 |
| FR-5 | 字体菜单以 `NSFont.displayName` 展示，内部仍以 PostScript name 识别与加载 | 切换字体观察显示与生效 |
| FR-6 | Bundle ID 恒为 `com.wonderassembly.compositor.cn`，不与官方冲突 | 读取 Info.plist |
| FR-7 | 不出现官方 Sparkle「检查更新…」入口（`startUpdater()` 永不调用） | 应用菜单检查 |
| FR-8 | 由 Compositor-CN Updater 负责更新，具备更新前事务状态与失败回滚 | 隔离演练（历史记录） |
| FR-9 | 每个官方版本的新增功能完整合入（示例 1.4.1：尺寸吸附、Move 栏即时应用、图层蒙版、取消编组、标签页排序与溢出、Command 临时反转 Auto Select、画笔错误提示、缩放比例显示） | 对照官方发布说明逐项人工验收 |
| FR-10 | 快捷键编辑器显示中文化，但已保存的快捷键以稳定的英文 id 持久化，不因语言切换失效；搜索中英文皆可命中 | 改语言或重开面板验证自定义仍在 |

## 4 本地化规范（LN）

> 本节定义**要求**。具体怎么写代码（三条上屏通道、枚举、格式串、键命名、补词条流程、审计盲区）
> 见 `Compositor-CN-project-standards.md` §4，不要在两处各维护一套实现细节。

本项目的核心约束。本地化泄漏共有四类，验收时必须四类全部清零：

| 类别 | 定义 | 处置 |
| --- | --- | --- |
| ① AppKit 裸字面量 | `NSMenuItem`、`toolTip`、`accessibilityDescription`、`labelWithString` 等直接给字符串，不自动本地化 | 必须显式包 `localizedString()` |
| ② 运行时拼接 | 如 `"\(w) × \(h) px"`，静态扫描看不到 | 改为 `String(format: localizedString(...))` 格式串 |
| ③ 词条缺失 | 源码有、目录没有 | 补 `Localizable.xcstrings` 词条 |
| ④ 系统本地化资源 | SF Symbol 按 bundle 语言替换字形（如 `textformat` 在 zh-Hans 下为「格式」） | 改绘或改用非文字类符号 |

**词条与格式规则：**

- 格式化串使用 `%@`（字符串）、`%lld`（整数）等标准说明符；含多个占位符时可用位置说明符（如 `%1$lld × %2$lld`）。
- 术语必须统一，不得同一概念多种译法（术语参考见 §9）。
- 保留 Undo/Redo、Adjustment、Merge、Delete 等动态标题的既有中文逻辑；Camera RAW、Trim、图层效果、底部工具提示沿用既有翻译。
- 不能只加目录词条：AppKit 路径必须逐条确认实际显示路径已走 `localizedString()`。

**禁止项：**

- 禁止把字母 T 翻成「格式」或任何中文词。
- 禁止直接使用「全部 ours / 全部 theirs」或整文件覆盖处理合并冲突。
- 禁止绕过动态英文与真实 UI 检查，只靠目录缺失数判定完成。

## 5 非功能性需求（NFR）

| 编号 | 需求 |
| --- | --- |
| NFR-1 | 构建：Debug 与 Release 两种配置均可**零参数**构建成功（Release 不依赖命令行签名覆盖） |
| NFR-2 | 签名：ad-hoc（flags=0x2）；`ENABLE_HARDENED_RUNTIME = NO` |
| NFR-3 | 测试：完整 CompositorTests 全绿（0 失败）；断言使用 `localizedString()` 而非硬编码英文 |
| NFR-4 | 启动：产物安装前必须通过启动冒烟测试（进程存活 5 秒以上） |
| NFR-5 | 性能：正式版使用 Release 配置（优化开启），不得用 Debug 充当正式版 |
| NFR-6 | 可回滚：替换正式版前必须建立可校验的回退副本，旧版保留至新版验收通过 |
| NFR-7 | 防灾：每轮工作提交后建立离机归档（git bundle 与含 `.git` 的 tar.gz 并存） |

## 6 构建与发布流程

> 可复制的完整命令（建快照、合并、补词条、借 Terminal 构建、装机、归档、推送、故障处置）
> 见 `Compositor-CN-runbook.md`。

**测试：**

```bash
xcodebuild -project Compositor.xcodeproj -scheme Compositor -configuration Debug \
  -destination 'platform=macOS,arch=arm64' \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" test
```

> CompositorTests 目标要求本机没有的 Mac Development 证书，测试必须带上述签名覆盖；这是环境问题，不是代码问题。

**正式版构建：**

```bash
xcodebuild -project Compositor.xcodeproj -scheme Compositor -configuration Release \
  -destination 'platform=macOS,arch=arm64' build
```

**发布步骤：**

1. 记录分支 / HEAD / snapshot-tag
2. 备份旧 App 并校验
3. 构建并做启动冒烟测试
4. 替换 `/Applications/Compositor-CN.app`
5. 核对版本 / build / Bundle ID / 签名 / 启动
6. 任一步失败按回退副本恢复

## 7 验收标准（每轮适配 checklist）

1. **代码状态**：合并真正结束并形成可解释提交；无未解决冲突或冲突标记；差异检查通过。
2. **本地化**：String Catalog JSON 有效、缺失 zh-Hans 为 0；四类泄漏审计缺口为 0；关键 UI 人工检查。
3. **构建与自动测试**：Debug 与 Release 构建通过；完整 CompositorTests 记录本轮通过数，0 失败。
4. **测试版**：Info.plist 版本 / build 与中文 Bundle ID 正确；从产物直接启动，菜单无官方更新入口。
5. **人工验收**：复核动态标题、T 标识、字体名称；重点覆盖新版本新增功能与 Camera RAW、PSD/PSB、导入导出。
6. **正式安装**：通过可回滚流程替换，并核对安装后版本、Bundle ID、可执行文件与启动。

## 8 约束与已知风险

### 8.1 签名约束

本机无开发者证书，只能 ad-hoc 签名。Release 配置若误开 `ENABLE_HARDENED_RUNTIME`，会因 library validation 与内嵌 Sparkle 的 Team ID 不匹配而在启动时 SIGABRT。**即使有开发者证书也仍会失败**——Sparkle 是 ad-hoc、无 Team ID。若日后需要 Developer ID 公证，应改用 `com.apple.security.cs.disable-library-validation` 权限并保留 Hardened Runtime。

### 8.2 更新机制

Compositor-CN Updater 会拒绝脏工作区。合并提交后工作区干净，该保护随之失效；启动正式更新器前应自行确认分支与 HEAD。

### 8.3 备份与远端

`adapt-compositor-1.4.1` 已推送到 `origin`（`ERVINYU18/Compositor`），分支与每个 `vX.Y.Z-cn` 标签都在远端。推送必须显式走 Clash 代理（`127.0.0.1:7897`），直连 `github.com` 不通，见 `AGENTS.md` 第 9 步。

本地防灾仍以离机归档为准：`git bundle` 不含 `.git/config`，须与含 `.git` 的 `tar.gz` 配套使用。只保留最新一份归档 + 两级安装回滚点，删旧归档前必须校验引用覆盖。

### 8.4 测试环境

系统区域为 zh_CN，测试宿主解析 zh-Hans，故任何新增本地化都会命中硬编码英文的断言；测试断言须统一使用 `localizedString()`。

## 9 术语参考（节选）

> 完整术语以 `Compositor/Localizable.xcstrings` 的 zh-Hans 词条为准（当前 1515 条）。
> 本节只列容易翻错、或历史上改过译法的核心词。

译文一致性是验收项之一。下列为核心术语的既定译法：

| 英文 | 中文 | 英文 | 中文 |
| --- | --- | --- | --- |
| Layer | 图层 | Mask | 蒙版 |
| Hue / Saturation / Lightness | 色相／饱和度／明度 | Levels / Exposure | 色阶／曝光 |
| Vignette | 晕影 | Halation / Bloom | 光晕／泛光 |
| Color Range | 颜色范围 | Shadows / Midtones / Highlights | 阴影／中间调／高光 |
| Guided | 参考线 | Parametric / Three-Way | 参数／三向 |
| Perspective / Rectilinear | 透视／直线投影 | Fit | 适合 |
| Highlight Priority / Color Priority | 高光优先／颜色优先 | Paint Overlay | 绘制叠加 |
| Diffusion | 扩散 | Point / Auto / Custom | 点／自动／自定义 |
| Undo / Redo | 撤销／重做 | Save As | 存储为 |
| Group / Ungroup Layers | 图层编组／取消图层编组 | Select Subject | 选择主体 |
