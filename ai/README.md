# AI 开发入口

当前开发工作区已迁移至 WSL 的 `~/github/q2`（`/home/alon/github/q2`）。
后续源码修改、打包和构建均在此目录进行；Windows 原目录是旧副本，不再作为开发目标。

先读 [项目入口](../README.md)、[架构](../docs/architecture.md)、[编码规范](../docs/development.md)、[配置规则](../docs/configuration.md)，再进入对应子仓库。

- [Kernel 工作协议](kernel.md)：API、组件、生命周期、权限和验证。
- [APP 工作协议](app.md)：Lua、manifest、能力申请及打包。
- [Platform 接入规范](../docs/platform-development.md)：SDK、输入识别及 owner 调度。
- [Python 统一入口](../docs/python-entry.md)：平台预设、配置事务、编译/运行/烧录；不要另建重复配置源。
- [Linux 构建](../docs/linux-build.md)：ESP32-S3 交叉编译、WSL 环境和宿主缓存隔离。
- [Linux SDL2](../docs/linux-x86.md)：x86 UI、q2.linux.json、POSIX 存储/Web、libcurl HTTP/HTTPS；音频未实现，不要宣称其可用。
- [真实能力清单](../kernel/ai/capabilities.json)：保留在 Kernel 仓库，使独立契约检查无需父仓库；不要复制成第二份可漂移清单。

这里是开发辅助文档，未提供设备 AI 推理能力。根 AGENTS.md 管理整个产品，子仓库 AGENTS.md 管理本层；分别检查各仓库状态并提交，根仓库不自动提交子仓库源码。
