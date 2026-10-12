# 产品设备数据接入

统一协议与完整例子见 [Kernel data](../kernel/docs/data.md)，公开 C 入口为 include/q2/data.h。

根 q2.json 的 components.data 默认 true，生成 Q2_COMPONENT_DATA 控制 x86 是否注册组件。旧配置缺少该字段时，x86/kernel 补 true，host/ESP 最小入口补 false。关闭后 Homepage/Key Demo 退回兼容路径，未注册 data 能力。root app.grants 与 APP manifest 都要声明所需能力。

| 产品 key | 类型/单位 | 权限 | 当前 x86 来源 |
|---|---|---|---|
| system.clock.time | string / HH:MM | clock.read | Windows 本地时间，TTL 5 秒 |
| power.battery.percent | integer / percent，0..100 | power.read | 默认 unsupported；Web 可模拟 |
| power.battery.voltage_mv | integer / mV，0..20000 | power.read | 默认 unsupported；Web 可模拟 |
| power.battery.charging | boolean | power.read | 默认 unsupported；Web 可模拟 |
| wireless.wifi.connected | boolean | wireless.read | 默认 unsupported；Web 可模拟 |
| wireless.wifi.rssi_dbm | integer / dBm，-127..0 | wireless.read | 默认 unsupported；Web 可模拟 |
| wireless.ble.connected | boolean | wireless.read | 默认 unsupported；Web 可模拟 |
| wireless.ble.rssi_dbm | integer / dBm，-127..0 | wireless.read | 默认 unsupported；Web 可模拟 |
| wireless.bt.connected | boolean | wireless.read | unsupported |
| input.key.<NAME>.action | integer / 1单击2双击3长按 | input.keys | x86 手势识别，经 lifecycle 放行 |

Platform 的 x86/device_data.c 拥有时钟/设备 schema 与发布代码；keys adapter 注册产品按键。未实现的硬件明确发布 unsupported，状态栏显示 BAT --，只有用户在 Web 明确应用模拟后才发布有效的调试电量/信号/连接状态。data 的 wireless.read 与可执行 Wi-Fi/BT 操作的组件能力不同。

Homepage shell.lua 使用 q.data.get 初始化、q.data.subscribe 更新本地缓存，并在 Lua 中把原始值格式化成电量和连接图标文字。managed 产品不再给 LVGL 填充设备状态结构；旧 q2_lvgl_system_status / shell.get 快照接口仅保留给 data 关闭或 standalone 兼容使用。视图大小、锁屏模式和屏保计时仍使用 shell API。

新增数据：在 Platform 或通用组件里注册名称、类型、单位、TTL 和 capability，采样后从 owner publish；APP 申请权限并按名称 get/subscribe。通常无需改 Kernel 或 Lua 绑定。新增领域 capability 时，还需同步产品 grants、root q2.py 的 provider 能力预检以及 APP manifest；这些属于产品集成，不是 Kernel 的字段枚举。现有领域新增 key 不需要修改能力预检。

不要在 APP 获取时同步阻塞读取外设；命令/刷新请求另建异步组件 API。UI 业务层区分 0、false、nil，处理 not_found/unsupported/permission_denied/timeout。按键订阅不会绕过锁屏。

验证记录见 [data 验证](validation/data.md)。

Web 调试使用同一 owner 发布路径，实时刷新 TTL，正常值未变化不会重复通知。异常模式发布 io_error/timeout，停用恢复 unsupported；断开 Wi-Fi/BLE 后 RSSI 为 invalid_state。数据仅在当前进程保存。使用方法见 [Hardware Lab](../platform/x86/web/README.md)。
