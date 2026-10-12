# 根工作区重构验证（2026-10-09）

## 已验证

| 检查 | 结果 |
|---|---|
| 根 q2.py test / 默认 x86 构建 | Zig 0.13 + CMake 4.0.3 + Ninja，通过 |
| CTest | 6 套通过：产品配置、按键时序、logging、LVGL、APP 管理、keys |
| 配置测试 | 5 个测试用例，包含字段/类型/范围、重复属性、未知项、依赖/未实现能力拒绝、生成值与增量写入 |
| Kernel 边界/依赖 | 30 个可移植文件、65 个 API 注释、33 个组件方法、1274 个第三方文件哈希通过 |
| APP 工具 | 76 项通过，UUID/打包/出厂清单未改变 |
| 根 run.ps1 | 默认 Homepage 以 502×410 headless 运行 12 轮，退出 result=0，生成真实 framebuffer |
| 裁剪 x86 产品配置 | 320×320，按键时间 30/250/900 ms；storage/keys/apps/logging 关闭，SQLite 开启，构建及启动通过 |
| Lua 能力探针 | 断言 display 为 320×320、SQLite 可用，keys/apps/storage.private/system.log 不可用，通过 |
| 最小 host | 关闭显示/存储/按键/APP 管理/Web/SQLite，device-info 成功启动退出 |
| Platform 独立构建 | 仅指定 Q2_KERNEL_DIR 与工具链，未指定 Q2_GENERATED_DIR，完整编译通过 |
| Web 到 Lua 回归 | 原始边沿→时序→Lua、取消/失联、自定义键、HTTP 拒绝及正常退出通过 |
| Homepage 回归 | 启动/返回、单图标切换、背景持久化、图标降级和错误回主页通过 |
| ESP32-S31 | 新根入口 + 最小配置，ESP-IDF 6.2-dev、RISC-V esp-16.1.0，镜像 207888 字节，编译通过 |

按键算法 C 单元测试使用稳定的默认阈值；用户配置的校验/生成由产品测试覆盖，实际二进制尺寸和组件能力另由 Lua 探针检查。第三方源码及 Kernel C/Lua API 未修改。

## 构建与持久化边界

新构建在根 build/ 下；default、x86-minimal、host-minimal、platform-standalone、esp32s31 互相隔离。没有使用移动前 CMake 缓存，没有删除或自动迁移旧 LittleFS 文件，没有烧录设备。测试日志与临时探针位于忽略提交的 build/。

ESP 环境在移动后原有激活配置失效，本次仅为验证进程显式指定已有 SDK/Python/工具 PATH 和 ESP_IDF_VERSION=6.2，未安装或下载依赖，未修改全局环境。日常 ESP 构建仍应从正确激活的 SDK 环境进入。

四个仓库的源码与文档保持未提交状态；没有自动提交、推送、添加远端或创建 submodule。
