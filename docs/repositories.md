# 四仓库工作方式

q2 是产品集成仓库，通过 Git submodule 固定三个独立实现仓库的提交版本。
地址存放在 `.gitmodules`，源码和历史仍分别属于各自仓库；root 不包含其源码副本。

| 子模块目录 | GitHub 仓库 |
| --- | --- |
| kernel | git@github.com:0x616c6f6e/q2-kernel.git |
| platform | git@github.com:0x616c6f6e/q2-platform.git |
| app | git@github.com:0x616c6f6e/q2-app.git |

## 获取与切换版本

克隆根仓库时传 `--recurse-submodules`，Q2 地址使用根仓库实际的远端地址。
已有 checkout 在根目录执行：

```sh
git submodule update --init --recursive
git submodule status
```

更新根仓库或切换其分支后再次执行 update，恢复根 commit 固定的子仓库版本。
不要用 `git submodule update --remote` 替代固定版本初始化：它会追踪远端版本，而不是产品记录的 commit。
子模块初始化后通常处于 detached HEAD；需要开发时，在该子仓库创建或切换工作分支再提交。

## 提交与发布

```sh
git status
git -C app status
git -C kernel status
git -C platform status
```

先在发生源码变更的子仓库提交，再从根目录执行 `git add app kernel platform` 并提交引用更新。
跨仓库契约变更同步记录各层的提交说明和验证结果。根 commit 保存 gitlink SHA，只有更新引用时
才改变产品使用的子仓库版本；子仓库工作目录出现未提交修改不会被根 commit 收录。

发布时先推送各子仓库包含被引用提交的分支，再推送根仓库，确保其他人能下载所有固定版本。
本地创建引用不会自动推送，也不能证明引用的 commit 已在 GitHub 上发布。
子仓库仍可单独克隆和构建；`q2.json.repositories` 可以指定其他相对根目录或绝对路径。

## 目录边界

根 README/AI/架构文档属于整个产品；Kernel 的公开 API、组件契约、机器能力清单和第三方来源
属于 Kernel，APP 的 manifest/打包协议属于 APP，Platform 后端协议属于 Platform。
独立克隆后的构建不依赖父目录文档。新增子模块或更换远端应有明确需求，不能仅因发现嵌套目录
就自动创建引用。

build/、dist/、缓存与实际介质属于生成内容，均忽略提交。旧位置的构建目录不删除，避免误删
调试数据或 LittleFS 偏好；也不拿旧的绝对路径 CMake 缓存当新工程构建结果。
