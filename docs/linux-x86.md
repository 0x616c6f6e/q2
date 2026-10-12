# Linux x86 / SDL2

Linux 桌面与 WSLg 现在使用 `platform/x86/window_sdl2.c` 输出同一套 Kernel/Lua/LVGL UI。
不需要 ESP-IDF；SDL2 仅属于 Platform，Kernel 和 Lua APP 不依赖 SDL 头文件。

## 安装与运行

Ubuntu / Debian：

```bash
sudo apt-get update
sudo apt-get install build-essential cmake ninja-build python3 libsdl2-dev pkg-config libcurl4-openssl-dev ca-certificates
cd ~/github/q2
python3 q2.py build --target x86
python3 q2.py run --target x86
python3 q2.py run --target x86 --app settings
python3 q2.py run --target x86 --app key-demo
```

要求 Python 3.10+、CMake 3.22+、SDL2 2.0.18+、libcurl 7.68+ 和 C11 编译器。
libcurl 必须支持 TLS 与异步 DNS（Ubuntu 系统包符合要求）。
也可用 `bash build.sh --target x86` / `bash run.sh --target x86`。
Bash 脚本不带 `--target` 时仍以 ESP32-S3 为默认目标；Python 入口默认目标是 x86。
不要在 Linux 使用 Windows `.exe` 工具链。WSL 需要 WSLg，普通 Linux 需要 X11 或 Wayland 会话。

窗口使用设备逻辑分辨率，可以缩放；SDL2 保持比例并映射鼠标坐标。鼠标点击/拖动驱动 LVGL，
滚轮滚动设置列表，Esc 返回主页（单 APP 模式则退出）。关闭窗口正常回收应用和文件锁。
窗口输入在 owner 线程处理，焦点丢失会松开鼠标，避免控件一直保持按下状态。

## 配置和能力

Linux x86 默认使用根目录 [q2.linux.json](../q2.linux.json)，Windows 默认仍为 q2.json，
ESP32-S3 默认仍为 q2.esp32s3.json。显式 `--config <file>` 可以覆盖，不会合并配置。
Linux 配置包含屏幕分辨率、字体、组件开关、按键时间、Web 端口和系统 UI 默认值。
初始分辨率沿用当前产品的 448×368；修改 display.width/height 后重新构建。
匹配分辨率的 assets/WIDTHxHEIGHT 图标优先，缺失时使用基础图标。

| 能力 | Linux x86 |
|---|---|
| LVGL、中文字体、出厂主页、设置、多 Lua APP | 支持 |
| 鼠标输入、滚轮、Esc 返回、BMP 截图 | 支持 |
| 命名按键及单击/双击/长按 | 支持，通过 Web Hardware Lab 模拟 |
| 本地 LittleFS 持久化 | 支持，256 KiB 文件、进程独占锁 |
| 电池/Wi-Fi/BLE 状态调试 | 支持，明确为模拟值，不代表真实设备连接 |
| HTTP/HTTPS 客户端 | 支持，libcurl 工作线程，GET / JSON POST / 原生二进制响应 |
| MP3 音频播放 | 尚未移植，Linux 配置关闭 audio |
| 真实 Wi-Fi/BLE 控制、USB 设备 | 尚未实现 |

Web 后台仍仅监听 `http://127.0.0.1:8765/`，包含按键和设备数据调试，不包含屏幕预览或触摸。
保留 Host/Origin/token 校验。Web 服务与 network 客户端是独立能力。
默认开启 components.network 并授予 network.http，Network Test 可直接使用电脑已有网络。
音频仍未移植，依赖 audio.playback 的 APP 不能启动；启用 audio 会明确拒绝构建。

产物为 `build/linux/x86/bin/q2_x86`。默认介质为 `build/linux/x86/app-data.lfs`，
不会覆盖 Windows 或 ESP 构建/存储。只有新介质会格式化，已有损坏文件会报错并保留原内容。
可用 `--storage-file <path>` 指定其他介质；不允许多个模拟器同时修改同一个文件。

## 无桌面运行与验证

```bash
python3 q2.py run --target x86 --headless --frames 80 --disable-web \
  --capture build/linux/x86/home.bmp
python3 q2.py test --target x86
python3 platform/x86/test_web.py --runner build/linux/x86/bin/q2_x86 --app-root app
python3 platform/x86/test_web_data.py --runner build/linux/x86/bin/q2_x86
```

`--headless` 不初始化 SDL 视频驱动，适合 SSH/CI；`--frames` 限制 owner 循环次数，不是显示刷新率。
SDL dummy 驱动测试还会验证真实 SDL 事件分发。硬件显示驱动、功耗和实际触摸性能不由 PC 测试证明。

## 独立 Platform 构建

在 platform checkout 内执行，无需父级产品配置：

```bash
cmake -S x86 -B build/linux-x86 -G Ninja -DQ2_KERNEL_DIR=/absolute/path/to/kernel
cmake --build build/linux-x86
ctest --test-dir build/linux-x86 --output-on-failure
```

Linux 独立后端开启 network，仅关闭未实现的 audio。完整产品通过 Q2_GENERATED_DIR 注入选定的根配置；
不要改 generated 头文件来覆盖能力检测。独立程序运行时必须显式提供 manifest、打包 Lua 和 grants。

## Linux 网络

```bash
python3 q2.py run --target x86 --app network-test
python3 platform/x86/test_network.py --runner build/linux/x86/bin/q2_x86
# 可选：自签名 TLS 拒绝测试需要 Python cryptography
python3 platform/x86/test_network.py --runner build/linux/x86/bin/q2_x86 --tls
```

点击 Start / PLAY 才发起请求。若修改过配置，须同时开启 components.network、授予 network.http；
manifest 也需申请该能力。重新编译并重启旧进程后，新配置才会生效。

后端为 platform/x86/network_curl.c，使用 ABI 2 和同一套 Kernel 网络接口。
URL/POST 数据立即复制到私有任务；工作线程拥有 curl handle，owner 通过 C11 acquire/release
读取完成结果，不在 UI poll 中等待 DNS/TCP/TLS。release 仅取消并分离；回收通过非阻塞 tryjoin；
最终 shutdown 最多等待 11 秒，超时保留后端并返回 busy，不强杀线程。

最多四个任务、响应最多 256 KiB、POST 最多 8 KiB，沿用 Kernel 的实例隔离和超时规则。
TLS 使用系统 CA 并检查主机名；无自动跳转、隐式 Cookie/认证和环境代理。
30x/404/500 作为正常 HTTP 响应返回，TLS 证书失败为 permission_denied，解析失败为 not_found。
取消后未退完的线程仍占槽，短时间重试可能得到 busy。Linux 音频和 Wi-Fi/BLE 控制不因此启用。

实现依据：[libcurl 线程规则](https://curl.se/libcurl/c/threadsafe.html)、
[进度与取消回调](https://curl.se/libcurl/c/CURLOPT_XFERINFOFUNCTION.html)。
