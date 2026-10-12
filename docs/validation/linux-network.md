# Linux network 验证（2026-10-11）

问题：SDL2 Network Test 显示 Network unavailable / permission denied。
原因：上一版 Linux 产品关闭 network，且未注册 Linux 网络传输，并非检测到用户网络断开。

本次新增 libcurl/pthreads 传输，启用 q2.linux.json 的 network 及 network.http grant。
Windows 继续 WinHTTP；Kernel/APP API 未改变，音频保持禁用。

- Ubuntu WSL，libcurl 8.5.0，系统 CA；异步 DNS/TLS feature 检查通过。
- 产品 CTest：16/16 通过；Kernel contracts、268 APP checks 通过。
- 实际 Lua HTTP：GET、查询参数、分片读取、404、禁止自动跳转、超限、文本 NUL 拒绝。
- 实际 Lua POST：分段构造 JSON、正确 Content-Type、精确回显、JSON Pointer 取值。
- 自签名 TLS：返回 permission_denied，未关闭证书校验或修改系统信任库。
- 延迟响应：超时期间 UI tick 持续执行；取消后句柄立即失效。
- 原生并发：四个并发槽、第五个 busy、URL/POST 调用后可修改源缓冲、释放后复用槽。
- 原生二进制响应保持 NUL；取消不等待慢响应；shutdown 回收线程。
- SDL2 Network Test 实际窗口自动点击 Start：HTTPS example.com 返回 HTTP 200，约 645 ms。
  日志与 BMP 位于 build/linux/x86/network-ui.log、network-https.bmp。

测试不代表 Wi-Fi/BLE 控制、音频播放或 ESP32 网络移植完成。未进行 Windows 重新编译。
