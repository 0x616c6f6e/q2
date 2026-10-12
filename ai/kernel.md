# AI 开发与能力约束

这里的“AI 能力文档”用于让开发助手准确理解项目边界、接口和验证要求；当前没有在设备上内置大模型推理或云端 AI 客户端。

入口顺序：README → architecture → 任务相关公开头文件 → kernel/ai/capabilities.json → components/lua-api → validation。能力清单中的状态属于工程事实，不能把 planned 当作可调用 API。

## 给开发助手的工作协议

1. 明确当前任务属于 Q2-Kernel、Q2-Platform 或 Q2-App，只在所属层实现。
2. 提出最小契约扩展；优先复用统一组件注册和结果码，避免新增 SoC 特例开关或平行框架。
3. 先读实际代码和调用方，公共 API 添加注释，解释校验、生命周期、资源释放及并发边界。
4. 针对修改运行真实验证，说明命令、结果和未验证范围。Mock DCD、RAM Flash、交叉编译均不能描述为实机验证。
5. 不自动格式化介质、不触发烧录、不改 CAD，不为满足测试伪造成功返回值。
6. 同步 capability、manifest、Lua 文档和示例；用户显式授权始终优先于本文件的工作建议。
7. 诊断复用 q2/log.h；不要把 SDK 日志带进 Kernel。新增日志不得依赖参数副作用，必须兼容 Q2_ENABLE_LOG=OFF；Lua 日志需要 system.log 授权，不能由 APP 改宿主开关。

## 可复用任务提示词

```text
为 Q2-Kernel 增加 <组件>。先阅读架构、公共头文件、AI 能力清单与开发规范。
使用统一 q2_component_t 注册；只有必要的硬件操作放在 Q2-Platform。
API 统一返回 q2_result_t，声明资源所有权和 capability，提供 Lua 通用方法表。
实现参数/权限/生命周期错误处理和 release_app，不访问其他 APP 数据。
补充有意义的集成测试、API 文档、能力清单，并报告真实验证和限制。
不要把尚未实现的后端注册成可用能力。
```

机器清单是文档契约而非 runtime 权限数据库；运行时仍以注册的 READY 方法和产品授权为准。`kernel/scripts/check_contracts.py` 检查清单与源码方法是否一致、公开返回值注释、SDK 边界及第三方文件校验，不是完整静态分析器。

应用导航变更须阅读 application-manager.md，更新 kernel/ai/capabilities.json；不得在 Lua 回调中关闭当前 VM。factory 身份只能来自产品注册；APP 切换保留其他 VM；仅目标重新启动时清理其旧实例资源。退出顺序为 apps_shutdown → caller Home runtime → kernel → providers。验证 q2_apps_contracts 以及真实 PC 首页/设置切换测试。

按键组件遵循 kernel/docs/keys.md：事件为单击/双击/长按，不是 GPIO 电平或 DOWN/UP。不要在 Kernel 加入时间判断、消抖、连击合并或按键功能映射；识别放 SoC，功能放 APP。订阅随 instance 回收，溢出必须报告。

系统策略由常驻 Homepage lifecycle Lua APP 实现；Kernel 提供独立场景、固定层级、授权和输入路由。普通 APP 只能绘制自身内容区，不能覆盖 status/saver。维护 owner 契约，修改时同步 system-ui 文档、test_multi_runtime.c 和 test_lifecycle_ui.py；验证双击 POWER 解锁不穿透、隐藏 APP 不可续期、任一 APP 故障不终止其他 VM。standalone 原生兼容路径仍由 test_system_ui.c 覆盖。

通用数据遵循 kernel/docs/data.md：复用 q2_value_t，不为每个字段增加 Core 枚举。新增字段放 provider；坚持 per-key 权限/owner 身份、无效和过期语义、退订/退出清理。state 可以合并/重试，event 不可合并。按键不得额外公开 raw 主题，锁屏需同时测 data.event 与 legacy last。验证 q2_data_contracts 和 test_lifecycle_ui.py。

网络遵循 kernel/docs/network.md：Kernel 不调用 socket/WinHTTP；所有后台 I/O 由 Platform 持有，get/status/read 不阻塞。请求按 instance 隔离、关闭与退出必清理；同步 WinHTTP 正在执行时不能跨线程关闭句柄。勿把 network.http 等同 wireless 控制、二进制下载或 OTA。
