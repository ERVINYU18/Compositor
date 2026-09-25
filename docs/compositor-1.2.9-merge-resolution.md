# Compositor 1.2.9 中文适配：合并冲突记录

适配分支：`adapt-compositor-1.2.9`
合并来源：`compositor-upstream-snapshot`（`v1.2.9`，snapshot HEAD `99d171b`）
适配基线：简体中文版 `1.2.6 (21)`，HEAD `5f49a72`

## 六个冲突及处理决定

| 文件 | 官方 1.2.9 变化意图 | 中文版要求 | 解决方式 |
| --- | --- | --- | --- |
| `Compositor.xcodeproj/project.pbxproj` | 更新官方营销版本和构建号 | 保持 `com.wonderassembly.compositor.cn` | 采用官方 `1.2.9` / build `24`，保留中文版 Bundle ID。 |
| `Compositor/IO/ImageExporter.swift` | 按文档像素预算与最大边动态限制导出尺寸 | 提示文案简体中文 | 保留官方限制逻辑，以本地化格式串呈现错误。 |
| `Compositor/IO/ImageImporter.swift` | 导入前按动态文档预算限制资源占用，并更新格式提示 | 中文提示，支持 PSD / PSB | 保留官方预算算法；本地化限制提示，并明确列出 PSD/PSB。 |
| `Compositor/IO/PSD/PSDDocumentBuilder.swift` | 保留 1.2.9 可编辑文字图层构建与回退行为 | 警告、字体回退信息简体中文 | 保留官方 PSD 构建实现，补上对应的本地化消息路径。 |
| `Compositor/IO/PSD/PSDTypes.swift` | 以通用“不支持的格式版本”语义适配新版 PSD/PSB 支持 | PSD/PSB 解析错误简体中文 | 保留新版通用错误分类与格式能力，本地化所有用户可见错误。 |
| `Compositor/IO/ProjectStore.swift` | 更新项目格式支持范围及动态资源预算 | 格式/资源错误简体中文 | 保留官方支持版本范围和预算实现，本地化错误提示。 |

## 相关保留与验证

- 保留简体中文资源、`zh-Hans` 与中文版 Bundle ID。
- 从官方配置中移除 Sparkle 更新 feed、自动检查等入口，避免启用官方更新流程。
- 保留 Undo/Redo、Adjustment、Merge、Delete 的动态标题本地化，以及 Blend Mode 的本地化名称与稳定枚举映射。
- PSD 新实现支持可编辑文本图层；为 PSB 注册导入类型，并保留导入、导出及格式错误的中文提示。
- 所有需要翻译的 String Catalog 项均应有 `zh-Hans`。动态英文检查不能只依赖静态 SwiftUI 字符串目录收录。

## Updater V2.1/V2.2 决定

本轮不添加自动冲突解决规则。V2.1 已有规则覆盖特定的 `CompositorApp.swift`、`BlendModePicker.swift` 和项目字符串目录；本轮的 PSD 构建、PSD 类型、导入导出和项目存储冲突改变了格式能力、资源限制或持久化语义，不能只凭文件名或文本替换安全自动合并。`project.pbxproj` 虽可逐项校验版本和 Bundle ID，但独立增加这一条规则不能覆盖其余未知冲突，也没有足够收益。

因此 Updater 应继续对这些路径停止并事务回滚。V2.2 只有在新增规则能验证明确的结构不变量、且有成功与失败样例证明不会吞掉未知冲突时再加入；未知文件或结构仍须停止并回滚。正式 App 安装必须继续等待用户完成测试并明确确认。本次没有修改正式 V2.1 Updater。

## 合并后的动态界面扫描修正

启动测试版并创建临时画布时，发现图层列表的 AppKit 右键菜单、辅助功能标签和提示文本仍使用英文常量。已在 `Compositor/UI/NativeLayerList.swift` 将这些 UI 字符串改为显式本地化，并为非空目录键补齐 `zh-Hans`；图层名称本身仍作为项目内容保留。按 V2.1 相同扫描规则对比 1.2.6 基线，发现数从 16 降至 5，没有新增项。
