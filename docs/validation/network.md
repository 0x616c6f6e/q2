# x86 Network 验证（2026-10-09）

新增可移植 network 组件、Windows WinHTTP 工作线程后端、可选 network.http 能力、根配置 components.network 与 Network Test APP。测试使用独立临时 APP/文件/端口；公网验证只请求 example.com，无用户凭据。

| 检查 | 结果 |
|---|---|
| Windows 构建 | Zig 0.13 / CMake / Ninja，first-party -Wall -Wextra -Werror 通过 |
| CTest | 10/10，包括新增 network 契约 |
| Network 契约 | 50 项；所有权、权限、错误 URL、请求配额、单实例限制、读分片、截止时间、退出回收 |
| UBSan | 独立编译 Kernel core + network + test_network，50 项通过 |
| 实际 HTTP | 真实 WinHTTP 与 Lua；查询参数、706 字节分片读取、404、302 不跳转通过 |
| 失败路径 | 16 KiB 上限、NUL 二进制拒绝、150 ms 超时、取消后句柄失效通过；超时期间 Lua 仍多次 tick |
| TLS | Network Test 真正访问 https://example.com/ 返回 200（一次观测 1656 ms）；临时自签证书拒绝为 permission_denied，未安装证书或关闭校验 |
| APP | 实际 LVGL/Lua 启动、HTTPS 按钮请求、无 network.http 授权时显示降级提示通过；已加入出厂目录中的普通 APP 列表 |
| Lifecycle | Home、多 VM、设置滚动/持久化、锁屏截键、双击解锁、屏保续期通过 |
| 契约与包 | 34 portable files、88 public APIs、54 component methods、1274 vendor checksums；81 APP 工具检查，六个 APP 打包通过 |

Network API 增加运行时绑定后，System settings 旧 64 KiB Lua 配额不足，回归捕获了 out_of_memory；调整到 96 KiB 并更新版本为 0.4.2 后全量 lifecycle 验证通过。未更改全局 Lua 配额或绕过内存限制。

[实际 HTTPS 画面](../images/network-test.png)。响应区域和 Home 按钮可滚动查看。

在 q2 根目录：

```powershell
ctest --test-dir build/data --output-on-failure
python kernel/scripts/check_contracts.py
python app/scripts/test_apps.py
python platform/x86/test_network.py --runner build/data/bin/q2_x86.exe
# 可选 TLS 拒绝测试需 Python cryptography，仅生成临时自签证书
python platform/x86/test_network.py --runner build/data/bin/q2_x86.exe --tls
python app/scripts/test_lifecycle_ui.py --runner build/data/bin/q2_x86.exe --artifacts build/network-test/lifecycle
```

范围：Windows 使用已有网络的文本 GET；不包含 Wi-Fi/BLE、代理配置、POST、socket、二进制文件、下载管理和 OTA。未验证 ESP32 实机。有效证书的公网请求需要当前网络可达，不作为离线可重复测试的必需依赖。停用 components.network 后不注册提供者；旧配置缺此字段默认 false。
