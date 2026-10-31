# 更新器回归演练（tools/updater）

这两个脚本不碰真仓库。它们在 `/tmp` 下建一次性 git 仓库，模拟「CN 分支 + 官方快照分支 +
snapshot-tag」的形状，然后直接 source 已装更新器的 `UpdaterCore.sh`，只测
`handoff_for_localization` 这一个函数。

## 为什么有这组测试

V2.2 原本在两道本地化门禁（新增动态英文、词条缺 zh-Hans）上直接 `fail` → 整笔回滚，
把已经合并好的成果全扔掉。1.5.6 和 1.5.7 都因此白跑一轮。V2.2.1 改成「停在 wip 分支」，
这是动仓库行为的改动，必须有回归。

## 跑法

```bash
bash "tools/updater/test-handoff-parks-merge.sh"
bash "tools/updater/test-handoff-refuses-conflict.sh"
```

两个都输出 `REHEARSAL_OK` / `REHEARSAL2_OK` 才算过。

## 各自验什么

**`test-handoff-parks-merge.sh`**（正常路径，11 条断言）

- 建出 `wip-cn-<tag>-needs-localization` 分支
- 该提交是**双亲合并提交**（`git rev-list --parents` 三列）
- 当前分支回到更新前 HEAD，分支名不变，工作区干净，无 `MERGE_HEAD`
- `snapshot-tag` 与快照分支都还原成更新前的值
- wip 分支里既有上游新文件，也有两边合并后的内容
- 退出码 `3`

**`test-handoff-refuses-conflict.sh`**（安全路径，9 条断言）

两边改同一行造真冲突，然后调 `handoff_for_localization`：

- **不建 wip 分支**（否则会把 `<<<<<<<` 提交进去）
- 走回滚：HEAD、工作区、`MERGE_HEAD`、`snapshot-tag`、快照分支全部复原
- 文件里没有冲突标记
- 退出码 `1`

## 注意

- `pause_exit` 会 `exit`，测试里必须把调用放进**子 shell** `( ... )`，否则测试脚本自己会被退出。
- 脚本里 `rm -rf /tmp/handoff-*` 是重建用的临时目录，不是项目文件。
- 用 `bash` 跑，别用 zsh 内联 source（`read -p` 和 ERR trap 在 zsh 下行为不同，会报假错）。

## 改更新器的流程

1. 先备份到 `~/Desktop/AI/DSH/Compositor CN/.Compositor-CN-Backups/Updater-历史版本/`
2. 改 `Contents/Resources/update.command` 或 `UpdaterCore.sh`
3. `bash -n` 语法检查两个文件
4. 跑这两个演练
5. `codesign --force --deep --sign - "/Applications/Compositor-CN Updater.app"`
6. `codesign --verify --strict` 通过后，在仓库**已是最新**的状态下跑一次真实短路冒烟
   （此时它会在「当前已经包含官方最新版」处直接退出，不建事务）
