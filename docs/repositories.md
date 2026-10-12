# 四仓库工作方式

q2 是产品集成仓库，app、kernel、platform 是独立嵌套工作目录。当前均未配置远端，没有自动创建 submodule 或 gitlink。根 .gitignore 忽略三个 checkout，避免一次 git add 将独立仓库错误纳入根仓库。

```sh
git status
git -C app status
git -C kernel status
git -C platform status
```

提交时分别在发生变更的仓库操作。跨仓库契约变更需要同步提交说明和验证记录；根 commit 只携带产品配置/工具/文档，不会固定子仓库版本。发布前应记录三个子仓库的 commit SHA；有远端后可以再选择 submodule 或版本清单方案，目前不编造 URL 或 commit。

根 README/AI/架构文档属于整个产品；Kernel 的公开 API、组件契约、机器能力清单和第三方来源仍属于 Kernel，APP 的 manifest/打包协议仍属于 APP，Platform 后端协议仍属于 Platform。独立克隆后的构建不依赖父目录文档。

build/、dist/、缓存与实际介质属于生成内容，均忽略提交。旧位置的构建目录不删除，避免误删调试数据或 LittleFS 偏好；也不拿旧的绝对路径 CMake 缓存当新工程构建结果。
