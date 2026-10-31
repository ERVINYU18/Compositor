# 本地化工具（tools/localization）

每轮适配都要用的两个脚本，其余是历史留档。

## 每轮要跑的

```bash
cd tools/localization
python3 add_<版本>_keys.py      # 先复制上一版改 TRANSLATIONS
python3 audit_strings.py
```

**`add_<版本>_keys.py`** —— 往 `Compositor/Localizable.xcstrings` 补 zh-Hans 词条。新版本**复制上一版**
（当前模板是 `add_1_5_12_keys.py`），只改 `TRANSLATIONS` / `OBSOLETE` / docstring。脚本自带三道保护，
**不要绕过**：

1. 写入前把目录备份到 `backups/`（已被 `.gitignore` 忽略）；
2. 先验证「重新序列化 == 原字节」，不通过就拒绝写 —— 目录文件**末尾没有换行**，
   直接 `json.dump` 会把整文件重写；
3. 目录里还有 `<<<<<<<` 冲突标记时拒绝运行。

废弃键走 `OBSOLETE` + `still_referenced()` 双重检查：源码里还有引用就不删。

**`audit_strings.py`** —— 只读扫描，报告「进了 UI 但没有词条」的字面量。**它有三类盲区**：
`control("Choke", …)` 这类行内没有 `Text(`/`.help(` 的单词标题、枚举/变量承载的键、
AppKit setter。报 0 缺口只是起点，还要按 `docs/Compositor-CN-project-standards.md` §4.7 人工补扫。

结果写到 `audit-result.json`（已忽略，不入库）。

## 路径

两个脚本都从自身位置推算仓库根，也接受环境变量覆盖：

```bash
COMPOSITOR_CN_REPO=/path/to/repo python3 audit_strings.py
COMPOSITOR_CN_LOCALIZATION_BACKUPS=/path/to/backups python3 add_1_5_12_keys.py
```

## 历史留档（一次性脚本，不要拿来跑）

这些是过去某一轮用过的，依赖已经清理掉的中间文件或旧提交，留着只为查「当时为什么这么翻」：

| 脚本 | 用于 |
| --- | --- |
| `apply_translations.py`、`apply_1_4_5_keys.py`、`apply_shortcut_keys.py`、`apply_merge_regression_keys.py` | 1.4.x 时期批量打词条，读 `01-merge-scene-evidence/` 里的 `.before-*` 备份（已清理） |
| `fix_accessibility_labels.py` | 一次性修 `Linked` 词条与无障碍标签 |
| `classify_gaps.py`、`analyze_merge_resolution.py` | 1.3.7→1.4.1 那轮把缺口分成「既有」与「合并引入」，硬编码了当时的提交号 |
| `add_command_palette_translations.py` | 命令面板整块本地化 |

`add_1_4_9` → `add_1_5_12` 这条链是**有效历史**：每个脚本的 docstring 记了那一轮加了什么、
删了什么、**哪些看着像字符串但确认不翻**及理由。翻旧账先看它们，比翻 git log 快。
