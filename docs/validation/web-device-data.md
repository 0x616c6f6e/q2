# Web 设备数据模拟验证（2026-10-09）

本轮为 x86 本机调试后台增加电池、Wi-Fi、BLE 表单，走现有 Kernel data 注册/发布与 Lua get/订阅路径；未改 Kernel 协议。状态栏增加独立 BLE token，Settings 完整模板与产品默认值同步。未实现真实无线连接或电池采样。

| 检查 | 结果 |
|---|---|
| Windows x64 构建 | Zig 0.13、CMake/Ninja 构建通过 |
| CTest | 9/9 通过，含产品配置、输入、日志、LVGL、系统 UI、APP、多 VM、keys、data |
| Kernel 契约检查 | 32 portable files、85 documented APIs、49 component methods、1274 vendor checksums 通过 |
| APP 工具 | 76 项通过 |
| HTTP → Lua | 临时 APP、随机本机端口；真实 get 与订阅值/状态匹配，0% 和 false 保留原始类型 |
| 输入校验 | 范围、整数溢出、小数、非法布尔值、重复/缺失/未知字段拒绝，不改变模拟配置；token/Origin 拒绝通过 |
| 无线语义 | BLE/Wi-Fi 独立，断开连接后 RSSI invalid_state；经典 BT 保持 unsupported |
| 异常/缓存 | io_error、timeout、off 模式通过；连续运行超过 5 秒仍刷新 TTL，同值不重复通知 |
| Chrome 实际表单 | 输入草稿保留、应用、异常模式禁用数字输入、停用及恢复通过 |
| Chrome 按键与布局 | 鼠标单击/双击/长按、键盘重复与失焦取消、真实 Lua 投递通过；375 px 无横向溢出 |
| Lifecycle | resident Home、三个 VM、设置滚动/保存、锁屏截键、双击 POWER 解锁、前台屏保续期与后台拒绝通过 |

实际截图：[Hardware Lab](../images/hardware-lab.png)。仅测试隔离的临时包、介质及 Chrome profile，未写入用户运行介质。

在 q2 根目录运行：

```powershell
ctest --test-dir build/data --output-on-failure
python kernel/scripts/check_contracts.py
python app/scripts/test_apps.py
python platform/x86/test_web_data.py --runner build/data/bin/q2_x86.exe
python platform/x86/test_web.py --runner build/data/bin/q2_x86.exe --app-root app
python app/scripts/q2app.py pack app/apps/key-demo --output build/web-test/key-demo.q2app
node platform/x86/test_web_ui.mjs build/data/bin/q2_x86.exe build/web-test/key-demo.run "C:/Program Files/Google/Chrome/Application/chrome.exe" docs/images/hardware-lab.png
python app/scripts/test_lifecycle_ui.py --runner build/data/bin/q2_x86.exe --artifacts build/web-test/lifecycle
```

模拟值仅当前进程有效，启动默认 unsupported。RSSI 与电压可供 Lua 读取，但当前 Home 只渲染连接文字与电量。旧存储里的状态栏模板不被产品默认值覆盖；要显示 BLE，应在 Settings 选择含 `{ble}` 的完整模板。模式 timeout 是显式注入过期错误，不是关闭数据源等待真实采样超时。
