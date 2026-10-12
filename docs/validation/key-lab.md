# 圆盘按键与 x86 时序验证（2026-10-09）

当前链路：浏览器原始按下/松开 → x86 key_input.c 识别 → Kernel key.action 透传 → Key Demo Lua。Kernel 没有新增计时逻辑，Lua 仍接收 1/2/3 三种 action。无 Web 屏幕预览或触摸。

| 本轮检查 | 结果 |
|---|---|
| Windows x64 构建 | Zig 0.13 / CMake / Ninja，-Wall -Wextra -Werror 通过 |
| x86 时序单元测试 | 131 项通过，假时钟覆盖最短脉冲、单双击边界、第二次长按、长按只发一次、取消、独立状态、64 位时间、失败不重放 |
| PC CTest | 5 套全通过：新增 key_input，加 keys、apps、LVGL、logging |
| HTTP → x86 → Kernel → Lua | 单击、重复单击、双击、松开前长按、取消、自定义按键、失联释放、非法直接 action、Origin/Host/token、分段 HTTP、正常退出通过 |
| Chrome 实际页面输入 | 真正鼠标单击/双击/按住、空格键和重复 keyDown、窗口 blur 取消通过；四个事件在真实 Lua 日志中匹配 |
| 页面尺寸 | 1200×960 实际截图，375 px 视口无横向溢出且圆盘四向/中心位置正确 |
| Key Demo 画面 | HTTP 集成 framebuffer 显示 6 个事件，POWER=LONG、CUSTOM_1=DOUBLE |

历史记录的配置源现已迁移至根 q2.json；测试时为 20 / 300 / 800 ms。截图：[Key Lab](../images/key-lab.png)、[Key Demo](../images/key-demo.png)。浏览器测试是单独 Chrome headless 临时 profile，不使用用户浏览器会话。

以下命令在 q2 根目录执行：

```powershell
ctest --test-dir build/x86 --output-on-failure
python platform/x86/test_web.py --runner build/x86/bin/q2_x86.exe --app-root app
node platform/x86/test_web_ui.mjs build/x86/bin/q2_x86.exe dist/key-demo.run "C:/Program Files/Google/Chrome/Application/chrome.exe" docs/images/key-lab.png
```

UI 验证脚本需要 Node 22+（原生 WebSocket）与 Chrome；运行 Key Lab 本身不需要 Node。先用 run.ps1 或 q2app.py 打包 key-demo。

前一轮已经验证 Kernel UBSan、APP 包工具、主页管理和 ESP 最小入口；本轮只改 SoC x86 输入，不把之前的 ESP 编译视为本次实体按键验证。当前没有 ESP GPIO 驱动或实板按键测试。网络时序以本机 x86 收到边沿时刻为准。
