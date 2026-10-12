# 验证记录

## 设置 UI / PNG / 横屏修复（2026-10-09）

- 原样导入用户的 96×96 system-settings-icon 和 502×410 home-background；settings 0.2.0 增加背景入口、三种选择和设备信息页。
- Windows x64 构建通过；真实 LodePNG 解码、图片 UUID 隔离、COVER 背景、尺寸查询和可调按钮宽度等 LVGL 检查共 128 项通过；日志检查及 CTest 2/2 通过。
- 真实 settings Lua/LVGL 点击测试：默认背景、Midnight/Forest 切换、进程重启后恢复、恢复默认、拒绝存储授权时不改保存值；全部通过。
- settings / ui-demo 在 502×410、410×502、320×480、64×64 下运行通过；小屏显示提示。修复 ui-demo 固定 y=422 超出 410 高屏幕的错误。
- 腐败 PNG 拒绝启动；已有非 LittleFS 文件未被格式化或改写。打包器同步 assets 并清理生成目录中的过期资源，45 项 APP 检查通过。
- Kernel 158 项 UBSan 检查通过；边界检查 26 个 C/H、50 个公开 API、20 个组件方法和 1274 个 vendor 校验通过。
- ESP32-S31 最小目标交叉编译通过；Lua assert 抛出统一错误表时，现在保留 invalid_argument 等错误名，回归测试已验证，不再只报 non-string Lua error。
- PNG 模式的 LVGL 固定池为 4 MiB；ESP32 尚未接入此显示 provider，本次 PC 结果不代表实体屏幕或 Flash 实测。偏好仅作用于 settings APP，未实现系统桌面或跨 APP 主题服务。

复现：Q2-App/scripts/test_settings_ui.py --runner /absolute/path/q2_x86.exe。脚本使用独立临时介质，不覆盖日常设置。

## 可控日志增量验证（2026-10-09）

- 新增可选 sink 和 Q2_ENABLE_LOG 编译开关，默认 SoC 控制台 INFO，Kernel 未注册 sink 时保持静默。
- 日志 ON 的 46 项检查、OFF 的 19 项检查通过，包含 Lua 显式授权、格式串、截断、过滤参数不求值、sink 失败不改变启动结果及递归保护。
- x86 在 ON/OFF 两种构建下，日志及 LVGL 的 CTest 2/2 均通过；原 101 项 LVGL 检查保持通过。
- PC headless 实际运行验证 off/warn 无 stdout/stderr，info 输出生命周期，debug 记录 ui.click；编译 OFF 时指定 debug 仍静默，非法等级拒绝执行。
- run.ps1 使用 -LogLevel off 完成打包、配置、构建和运行；构建恢复为默认 Q2_ENABLE_LOG=ON。
- 原 Kernel UBSan 158 项检查通过；host 构建及 Q2_LOG_LEVEL=info/off 下 settings APP 实际执行通过。
- ESP32-S31 日志 ON/OFF 均交叉编译通过，已恢复 ON 并重新构建。未烧录，串口吞吐与硬件时序尚未验证。
- 契约检查：26 个第一方 C/H、49 个带注释公开 API、16 个组件方法和 1274 个第三方校验通过。

复现控制项及输出后端约束见 [日志](../../kernel/docs/logging.md)。后续历史记录的检查数量保持原样。

## LVGL / x86 增量验证（2026-10-09）

- 固定 LVGL 9.3.0，Windows x64 / Zig 0.13 / CMake 4.0.3 构建原生窗口运行端成功。
- 新增 101 项 LVGL 检查通过，CTest 1/1 通过：真实像素、鼠标输入到 Lua、权限拒绝、48 控件配额、旧句柄、文本接口复用、I/O 失败清理重试和二次创建。
- 原 Kernel 的 158 项 UBSan 检查通过；APP 打包测试扩展到 37 项并通过。
- ESP32-S31 最小工程增量构建通过；该目标仍默认关闭 LVGL，不增加其 RAM 负担。
- ui-demo 以 headless 模式渲染 30 轮；原生窗口运行 45 轮，并通过 WM_LBUTTONDOWN/UP 注入点击，确认 Lua 将 Play 更新为 Pause。实际 framebuffer 预览位于 q2/docs/images。
- `run.ps1` 完成打包、配置、构建和 headless 运行；显式传入独立 Kernel/App/工具路径。
- 架构检查通过：24 个第一方 C/H、44 个公开 API 注释、16 个组件方法、1274 个第三方文件校验。
- 仅验证 Windows x64，32 位 PC、Linux/macOS、中文字体和物理屏幕尚未验证。PC 渲染不代表 ESP32-S31 屏幕驱动或音频功能已完成。

下面保留引入 LVGL 前的基础版验证，Display 控制台限制现仅适用于 host/text provider；LVGL/x86 的范围以本节和 [图形组件文档](../../kernel/docs/lvgl-display.md)为准。

## 基础版验证

日期：2026-10-09。版本：Q2-Kernel 0.1.0 / Lua API 2。环境为 Windows，Zig 0.13 C 编译器、CMake 4.0.3、Ninja 1.12.1；ESP32-S31 使用本地 ESP-IDF v6.2-dev 和配套 RISC-V 工具链。没有实板。

| 检查 | 结果 | 覆盖范围 |
|---|---|---|
| Python host builder + UBSan | 158 项通过 | 真实 Lua、LittleFS、FatFs、SQLite、TinyUSB |
| 独立 Kernel CMake / CTest | 1/1 集成用例通过 | 另一路构建图，不依赖旧 firmware 源码 |
| Q2-App 工具测试 | 32 项通过 | 稳定 UUID、SemVer、权限、元数据、重复打包及摘要 |
| 独立 Host 工程 | 构建并执行两个示例 | 外部 Kernel 路径、真实 Lua、RAM 文件系统、文本后端 |
| ESP32-S31 最小工程 | 构建成功 | 生成 q2_kernel_esp32s31.bin，0x32360 字节 |
| 架构契约检查 | 通过 | 21 个第一方 C/H 文件、40 个公开操作注释、11 个组件方法、255 个依赖文件校验 |

核心测试包含：缺失依赖与环、重复注册、可选失败和必需阻断、事件队列满、过期 instance 丢弃、服务 ABI、权限拒绝、跨 UUID 数据隔离、输入和输出字符串边界、VM 错误/死循环/内存不足回收、显示所有权、清理失败重试、LittleFS/FatFs 重挂载读回，以及 TinyUSB GET_DESCRIPTOR 控制请求。

## 复现

```sh
# 在 Q2-Kernel 中
python scripts/check_contracts.py
python scripts/build.py --cc /path/to/zig
cmake -S . -B build/native -DQ2_BUILD_TESTS=ON -DQ2_WITH_SQLITE=ON -DQ2_WITH_USB=ON
cmake --build build/native
ctest --test-dir build/native --output-on-failure
# 在 Q2-App 中
python scripts/test_apps.py
python scripts/q2app.py pack apps/settings -o dist/settings.q2app
python scripts/q2app.py pack apps/device-info -o dist/device-info.q2app
# Host 和 ESP32-S31 命令见独立 Q2-Platform README
```

开发机沿用旧 firmware 中已安装的编译器作为命令行工具路径。新源码、CMake、APP 打包工具均不引用该目录；可以改用任意独立安装的兼容工具链。

## 验证边界

- RAM 模拟介质验证文件系统逻辑和同一内存的重挂载，不代表真实 Flash 掉电、擦写寿命或 SD 热插拔。
- TinyUSB 使用专用测试 DCD，只验证所列栈路径；ESP32-S31 物理 USB 未移植/未实测。
- SQLite 当前仅内存存储，不保证重启持久化；FatFs 写入没有原子替换保证。
- Host Display 是控制台文本后端，未验证 AMOLED/LVGL 渲染。
- ESP32-S31 固件只创建内核/runtime 并轮询，没有产品外设注册和 APP 自动装载。
- 没有验证真实音频、BT/PAN、手机兼容性、充电和硬件功耗；这些产品功能尚在旧 firmware。
- APP 包是可信开发产物；没有设备安装器、发布者签名校验或 OTA 回滚。

各项结果分别说明构建、模拟与实机范围，不能由该表推导为完整播放器已完成实机验证。
