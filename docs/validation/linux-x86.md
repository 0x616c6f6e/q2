# Linux x86 SDL2 验证

工作区：WSL Ubuntu `/home/alon/github/q2`。Linux 原生 GCC、CMake/Ninja、SDL2 2.30.0。
日期：2026-10-11。本次修改产品根仓库与 platform；未修改 Kernel、APP 或 ESP 显示驱动。

- `python3 q2.py test --target x86`：15/15 CTest 通过。
- Kernel contracts：38 portable files、92 documented APIs、69 component methods、1274 vendor checksums 通过。
- APP 工具：268 checks 通过。
- 独立 Platform 配置/构建：无 Q2_GENERATED_DIR，4/4 CTest 通过。
- SDL2 dummy + headless：RGB 字节序、矩形 stride、同步复制、截图、输入边界、焦点释放、滚轮、Esc、关闭与清理。
- POSIX assets：分辨率变体优先、fallback、坏资源拒绝、尺寸限制、符号链接拒绝。
- LittleFS：跨进程启动保留数据、独占锁、已有非法大小及同尺寸损坏介质不被格式化。
- Web 集成：单击/双击/长按、取消、输入租期、自定义按键、HTTP 权限拒绝和清理。
- Web data 集成：电池/Wi-Fi/BLE 数据、非法值、授权、TTL、隔离。
- WSLg 原生 SDL2 窗口：Homepage 运行 100 次 owner 循环并正常退出，BMP 画面已检查。
- Settings：headless 运行 80 次 owner 循环，前台进入设置、常驻主页与全部组件正常退出。
- clang-format --dry-run --Werror：本次 C 文件通过。
- Linux 显式使用启用 network/audio 的 q2.json 时，入口给出明确错误，未修改配置/旧存储。

运行产物位于 build/linux/x86/：linux-home.bmp、linux-settings.bmp、测试用 .lfs 与日志。
Windows 后端保留，但本轮未运行 Windows 编译；没有验证实际硬件。
Linux 的 HTTP 客户端与音频后端尚未移植，q2.linux.json 明确禁用；Web 调试服务器已实现。
