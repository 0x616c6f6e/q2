# 常驻 Lifecycle、状态栏与屏保

Homepage 是产品默认启动、始终驻留的 Lua lifecycle APP。每个普通 APP 使用独立 Lua VM，最多 8 个实例（含 Homepage）在同一 owner 线程协作运行。隐藏的 APP 继续收到自己的事件和 `on_tick(now_ms)`；这不是 8 个并行线程。普通 APP 退出释放自身资源，Home 无需重启。

## 显示与输入

固定层级从低到高：**主页 → 当前前台 APP → 屏保 → 已启用的状态栏**。打开 APP 隐藏主页内容；返回主页隐藏普通 APP 内容。各实例只能修改自己的控件，普通 APP 不能遮挡系统层。状态栏关闭时释放其占用的视口高度。

Homepage 的 `src/shell.lua` 负责状态栏内容、空闲计时、移动时钟和解锁规则；Kernel 提供隔离场景、权限校验、时间/状态快照、配置存储和定向输入转发。Platform 负责按键手势识别和实际硬件状态。

默认 30 秒无操作进入黑底移动时钟，每 10 秒移动一次。锁屏默认关闭；在 Settings 开启后，屏保进入锁屏，普通按键、触摸、滚轮和 Esc 不会传给前台 APP。默认 **双击 POWER 解锁**，这次双击被系统消耗，不触发 APP。非锁定屏保的首次有效输入只唤醒，并吞掉完整手势。

锁屏是防误触功能，没有密码认证、硬件休眠或屏幕断电。后台 APP 继续执行；不代表后台音频组件已经实现。

## 产品默认配置

根目录 `q2.json`：

```json
"system_ui": {
  "status_bar": true,
  "status_bar_height": 32,
  "screensaver": true,
  "idle_timeout_ms": 30000,
  "clock_move_interval_ms": 10000,
  "lock_enabled": false,
  "status_left": "{time}",
  "status_right": "{wifi} {bt} {ble} {battery}",
  "saver_text": "{time}",
  "unlock_key": "POWER",
  "unlock_action": 2
}
```

内容模板支持 `{time}`、`{battery}`、`{wifi}`、`{bt}`、`{ble}` 和普通文本，各字符串最多 127 UTF-8 字节。字体目前为拉丁字符 Montserrat，尚无中文字库。未知电量显示 `BAT --`；PC 默认电池与无线状态不可用，可在 Web 的设备数据面板明确输入模拟值。单击/双击/长按分别为 1/2/3，快捷键名称必须存在于 `keys.names`。

Settings 使用纵向可滚动列表：背景、状态栏开关及左右内容预设、屏保开关、空闲时间、移动间隔、屏保内容预设、锁屏开关及解锁手势。支持鼠标滚轮/拖动和 PREV/NEXT 单击滚动。任意文本模板可在 JSON 修改；页面提供常用预设。

有 LittleFS 时，设置保存到 Home UUID 的 `ui-*` 键，重启后覆盖产品默认值；无存储时仅会话有效。JSON 是出厂默认值，修改它不会覆盖已有用户偏好。坏的旧字段忽略，实际 I/O 故障返回错误，不格式化介质。若产品移除了已保存的解锁按键，本次启动禁用锁屏，避免无法解锁；需在设置中重新选择有效键。

默认物理尺寸 502×410，状态栏 32 px，APP 内容区 502×378。`q.ui.width()/height()` 已返回当前内容区，不要再次扣高度。状态栏切换向活跃场景发送 `ui.resize`；APP 应重新布局，保留业务状态。前台内容坐标相对内容区，Platform 输入仍使用物理坐标。

## 自定义屏保与歌词

普通 APP 声明可选 `screensaver.inhibit` 后，可在 `on_tick` 中持续调用 `q.shell.keep_awake()`，刷新系统空闲起点，自己绘制歌词等内容。调用仅限**当前前台、清醒且未锁定**的实例。返回 Home 后后台请求会被拒绝；已经锁定不能靠该 API 解锁。停止续期后按正常空闲时间进入系统屏保，不存在遗留的永久禁止屏保开关。

参考 [自定义屏保示例](../app/docs/custom-screensaver.md)。这次只提供机制，没有实现 MP3 解码或歌词下载。

## 平台接入

1. boot 前调用 `q2_lvgl_system_configure`、`q2_lvgl_lifecycle`，注册出厂 settings UUID。
2. 管理器 bind 的 VM 专供 Home。owner 每轮取得 `q2_apps_state`，调用 `q2_lvgl_focus` 和 `q2_keys_route`。
3. `q2_lvgl_system_status` 传入真实时间/电池/无线状态。Lua 空闲计时使用单调时钟。
4. 输入上报先经过 `q2_lvgl_activity`；非锁屏唤醒吞掉整个手势。锁屏时识别后的动作仍送给生命周期路由，由 Lua 判断双击 POWER，不能直接送普通 APP。
5. `q2_apps_shutdown` 后销毁绑定的 Home runtime，再销毁 Kernel 和 provider。

未启用 managed lifecycle 的 standalone 显示保留原生简易状态栏/屏保，供单 APP 调试和兼容测试；它没有 Lua 锁屏策略。ESP 最小入口尚未注册实际显示、按键或应用目录。

Web Hardware Lab 支持按键与电池/Wi-Fi/BLE 数据模拟。`/api/state` 可读 `lifecycle`、`locked`、`screensaver` 和视口尺寸，没有屏幕预览/触摸接口。

## 验证

```sh
python q2.py test --compiler zig
python app/scripts/test_lifecycle_ui.py --runner build/x86/bin/q2_x86.exe --artifacts build/lifecycle-ui
python app/scripts/test_homepage_ui.py --runner build/x86/bin/q2_x86.exe --status-bar-height 32
python app/scripts/test_settings_ui.py --runner build/x86/bin/q2_x86.exe --status-bar-height 32
```

新集成测试使用临时包、临时 LittleFS 和随机本机 Web 端口，验证真实独立 VM、隐藏 APP tick、分层、设置重启恢复、锁屏截键、双击解锁及前台续期/后台拒绝。旧 `test_system_ui` 验证 standalone 原生兼容路径。实测范围见 [验证记录](validation/lifecycle.md)。

设备状态已迁移至通用数据组件：默认 managed 产品的电量/时钟/无线值来自 q.data 订阅，Homepage 在 Lua 中格式化。旧显示 status 结构只保留兼容路径。数据不可用显示未知；见 [产品设备数据](device-data.md)。
