# Homepage 验证记录（2026-10-09）

> 此为早期版本验证记录；当前常驻多 VM / Lua 屏保行为见 [Lifecycle 验证](lifecycle.md)。

## 0.2.0 横向单应用主页

主页改为一次只展示一个应用：中央等比例图标、下方居中名称、两侧透明箭头，首尾循环切换，无状态栏。preview 图片已替换为实际 502×410 渲染。

验证：APP 打包 71 项通过；PC CTest 三套通过（LVGL 273、应用管理 57、日志 46 项）；真实 UI 集成覆盖左右切换/首尾循环、打开目标、返回主页、不同尺寸及设置背景持久化。原设置页完整 UI 回归通过。新增布局参数向后兼容，未变更 SoC 的公开 C 接口或硬件。


本次新增主页与前台管理，未改变硬件工程，未执行烧录。

| 检查 | 结果 |
|---|---|
| Windows x64 Zig 0.13 / CMake / Ninja 构建 | 通过 |
| Kernel 可移植集成测试，UBSan | 158 项通过 |
| 应用管理 C 契约 | 57 项通过 |
| LVGL 实际渲染/输入/资源释放 | 152 项通过 |
| 日志契约，编译 ON | 46 项通过 |
| APP 打包、稳定 UUID、出厂清单拒绝路径 | 63 项通过 |
| 架构与能力清单检查 | 28 个可移植文件、58 个公开 API、29 个组件方法、1274 个供应源码校验通过 |
| Windows 默认 run.ps1，不传 AppName | 从 Homepage 启动，退出 result=0 |
| 主页真实 Lua/LVGL UI 集成 | 图标/名称、进入设置、共享壁纸跨进程保存、四轮切换、分页、坏图标降级、普通 APP 启动/事件故障回主页、主页故障退出、非出厂写权限拒绝通过 |
| settings 独立运行回归 | 图片、点击、保存、拒绝存储、四种分辨率、损坏介质/PNG 拒绝通过 |
| ESP32-S31 / ESP-IDF 6.2 最小入口编译 | 通过，镜像 207888 字节，未烧录 |

实际默认主页预览：q2/docs/images/homepage.png。测试使用临时 APP 副本和存储文件，不覆盖用户偏好。

当前为单前台 VM，切换结束旧 APP、重新启动目标。APP 目录启动前固定，上限 8，尚无后台运行/安装卸载/OTA；中文字体、实机屏幕和实体 Home 按键未验证。

复现入口：Kernel scripts/build.py、scripts/check_contracts.py；PC CMake 的 Q2_BUILD_APPS_TESTS、Q2_BUILD_LVGL_TESTS、Q2_BUILD_LOG_TESTS；App scripts/test_apps.py、test_homepage_ui.py、test_settings_ui.py。Python UI 测试用 --runner 指定编译后的 PC 可执行文件。
