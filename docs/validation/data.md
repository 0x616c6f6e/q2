# 通用数据组件验证

日期：2026-10-09。构建：Windows x86 / Zig 0.13 / CMake 4.0.3，root build/data。新增数据组件、typed event、动态领域权限与平台适配均使用第一方源码；未改第三方库、CAD、烧录或用户的默认持久介质。

## 结果

- x86 构建成功，CTest **9/9** 通过。
- 新增 q2_data_contracts：**204** 项，包含真实 Lua 运行。
- 独立核心 UBSan/Werror：**159** 项通过；Q2-App 打包工具 **76** 项通过。
- Kernel 边界/契约：**32** portable files、**85** documented C APIs、**49** component methods、**1274** vendor hashes。
- test_lifecycle_ui.py 通过；锁屏探针已改用 q.data 订阅，还在 on_tick 检查 legacy q.keys.last 不能看到被屏蔽的 POWER。
- 产品根入口打包并运行 Key Demo 40 帧成功；Home 使用订阅状态，Key Demo 使用通用按键主题。
- ESP32-S31 最小入口增量交叉编译通过（ESP-IDF v6.2-dev）；未注册实物 data provider、不烧录。日志 build/data-esp-build.log，复用 build/lifecycle-esp 构建目录。

## 关键覆盖

注册唯一性、owner 不匹配、类型/数值范围、读权限与退订归属、未知与零电量、相同值刷新不通知、TTL 到期及恢复、显式 I/O 失效、字符串拷贝、初始快照、待发状态合并、满队列重试、通知限频、连续相同事件不合并、事件溢出返回 LIMIT、每 APP 配额、退出/退订取消待发事件、前台切换清理受限事件、锁屏不泄露原始按键。

Lua 验证 bool false 是有效值、失效时 value=nil/status=io_error、通知带 key/subscription/sequence/timestamp；两个 VM 订阅同 key 时，一个退订/退出不取消另一个。产品真实 Web down/up 经 x86 双击识别后，双击 POWER 解锁被 Home 消耗，不触发普通 APP 的 data.event。

## 复现

在 q2 根目录，编译工具已在 PATH：

```sh
python q2.py build --build-dir build/data --compiler zig
ctest --test-dir build/data --output-on-failure
build/data/bin/q2_data_tests.exe
python app/scripts/test_apps.py
python app/scripts/test_lifecycle_ui.py --runner build/data/bin/q2_x86.exe --artifacts build/data/artifacts
python kernel/scripts/check_contracts.py
python kernel/scripts/build.py --cc zig
```

## 范围

PC 只提供真实本地时间和模拟按键；电池、Wi-Fi RSSI/连接、BT 连接通道明确 unsupported。注册读取通道不等于具备硬件驱动或控制能力。嵌入式采样、事件队列内存预算和 IRQ/工作线程桥接仍需随具体驱动实测。
