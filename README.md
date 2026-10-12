# Q2

Q2 的产品集成仓库：统一配置、构建/运行入口、公共开发文档和 AI 协作规则。三个实现仓库分别放在 `app/`、`kernel/`、`platform/`，其中原 SoC 层已更名为 Platform。

## 目录与 Git 边界

```text
q2/                       产品 Git 仓库
  q2.json                 唯一产品配置源
  q2.py                   configure / build / run / test / pack
  build.ps1 / run.ps1      Windows 简便入口
  build.sh / run.sh       Linux / WSL 构建与运行入口（默认 ESP32-S3）
  CMakeLists.txt          产品 CMake 入口
  scripts/                配置校验、生成与测试
  docs/                   架构、配置、构建、平台接入、验证和截图
  ai/                     AI 工作协议与能力文档导航
  app/                    独立 Git：Lua APP、manifest、资源与打包工具
  kernel/                 独立 Git：C11 Kernel、组件、API、固定第三方库
  platform/               独立 Git：x86 / host / ESP32-S31 平台适配
  build/<target>/          生成文件、程序和测试输出（不提交）
  dist/                   APP 开发包和 .run 目录（不提交）
```

`app/`、`kernel/`、`platform/` 通过 Git submodule 引用各自的 GitHub 仓库；`.gitmodules` 保存地址，根 commit 固定三个子仓库的版本。各层源码仍分别开发和提交，根仓库只记录它们的 commit 引用。克隆时使用 `git clone --recurse-submodules <Q2仓库地址> q2`，已有 checkout 执行 `git submodule update --init --recursive`。`q2.json.repositories` 仍可指向其他 checkout 路径。详见 [仓库管理](docs/repositories.md)。

## 构建和运行

需要 Python 3.10+、CMake 3.22+、Ninja 和 C11 编译器。x86 支持 Windows 原生窗口和 Linux SDL2；Windows 已验证 Zig 0.13。第三方库在 Kernel 内固定，不在构建时下载。

在 **q2 根目录** 执行：

```powershell
./build.ps1
./run.ps1
./run.ps1 -AppName key-demo
./build.ps1 -Test
```

如果工具不在 PATH，增加 `-Python <python.exe> -CMake <cmake.exe> -Compiler <zig.exe> -Ninja <ninja.exe>`。不要使用 Windows Store 的未安装 Python 占位程序；先安装 Python 或显式传入实际解释器。

通用命令：

```sh
python q2.py build --compiler zig
python q2.py run --app settings --compiler zig
python q2.py run --headless --frames 30 --capture build/home.bmp --compiler zig
python q2.py test --compiler zig
python q2.py pack
```

脚本默认构建 x86；配置、编译与 APP 打包失败都会以非零状态退出。`--target kernel` 构建独立 Kernel 契约；host/esp32s31 必须使用符合平台能力的配置，见 [配置规则](docs/configuration.md)。独立子仓库的 CMake/打包入口仍可用，不强制依赖根仓库。

从旧位置移动来的 build 缓存含绝对路径，**不要重用**。新入口从根 build/ 重新构建。原 platform/build/x86/app-data.lfs 不会删除、覆盖或自动迁移；需保留偏好时，可用 `q2.py run --storage-file <原文件路径>`，并先关闭占用它的旧进程。

Linux / WSLg：`python3 q2.py run --target x86`，默认读取 `q2.linux.json`。
依赖、输入操作与能力范围见 [Linux SDL2](docs/linux-x86.md)。

## 产品设置

编辑 [q2.json](q2.json)，再次构建或运行即可生效：

- 屏幕默认 502×410，顶部状态栏 32 像素；30 秒无操作进入黑底移动时钟屏保。
- 最短有效按下 20 ms、双击间隔 300 ms、长按阈值 800 ms。
- display、storage、keys、apps 默认开启，SQLite 默认关闭。
- 日志编译/等级、Web 硬件调试后台/端口、按键名称、启动 APP 和授权均集中配置。
- Windows 提供网络和音频后端；Linux SDL2 已支持 HTTP/HTTPS，音频暂未移植。USB 和真实无线控制尚未实现。

组件开关不会绕过 APP 权限；manifest 的 required 能力必须同时被产品允许且后端存在。

## 文档

[配置参考](docs/configuration.md) · [APP 分辨率适配](docs/app-resolution.md) · [状态栏与屏保](docs/system-ui.md) · [PC 运行](docs/x86.md) · [架构](docs/architecture.md) · [开发规范](docs/development.md) · [平台接入](docs/platform-development.md) · [迁移路线](docs/migration.md) · [AI 入口](ai/README.md) · [本次重构验证](docs/validation/workspace.md)

[Kernel API](kernel/docs/lua-api.md) · [组件契约](kernel/docs/components.md) · [APP 协议](app/docs/app-contract.md) · [Hardware Lab](platform/x86/web/README.md)

当前可运行 PC 主页、设置、按键模拟和 Lua APP。ESP32-S31 仍为最小入口，未完成产品外设迁移；PC 构建通过不代表实物播放器验证通过。


## 常驻系统 UI 与多应用

Homepage 是常驻 lifecycle APP，最多 8 个独立 Lua VM 协作运行。它负责主页、最顶层状态栏、空闲屏保及可选锁屏（默认双击 POWER 解锁）。Settings 为纵向滚动列表，系统 UI 默认值在 q2.json，用户偏好可持久保存。普通前台 APP 可持续刷新屏保计时实现歌词页面。

详见 [系统 UI](docs/system-ui.md)、[多应用管理](kernel/docs/application-manager.md)、[自定义屏保](app/docs/custom-screensaver.md) 和 [验证记录](docs/validation/lifecycle.md)。

通用 [设备数据](docs/device-data.md) 已提供按名称读取/订阅，区分缓存状态与离散事件；新增数据项通过平台注册，锁屏输入保持隔离。

网络调试：[Network Test APP](app/docs/network-test.md) · [Network API](kernel/docs/network.md)。Windows/Linux x86 已支持异步 HTTP/HTTPS GET 和 JSON POST，Wi-Fi/BLE 连接管理仍未实现。

## ESP32-S3 / AM1.78

在激活的 ESP-IDF 环境运行 `./build.ps1 -Target esp32s3`，默认选择根
[q2.esp32s3.json](q2.esp32s3.json)，输出 build/esp32s3，保留 PC 配置。
现阶段为 AM178/AM213 显示/触摸与正式 Homepage/Settings 入口，参考 N16R8；Lua/资源内置固件，尚未移植 Music 网络/音频等产品外设。
接线、内存假设、构建与实机待验项见 [平台说明](platform/esp32s3/README.md)。
Linux / WSL：先执行 `source ~/github/esp-idf/export.sh`，在 q2 根目录执行 `bash build.sh`。
输出到 `build/linux/esp32s3`，与 Windows 缓存隔离；详见 [Linux 构建](docs/linux-build.md)。
切换 ESP-IDF / Python 路径时，根构建入口会检测主工程及 bootloader 缓存，备份旧目录并保留
`sdkconfig` 后重新构建；详见 [构建缓存说明](docs/development.md#esp-idf-构建缓存)。

ESP32-S3 新增 [AM213 410×502 / CST820](platform/esp32s3/docs/am213.md)，使用独立根配置 `q2.esp32s3-am213.json`。
