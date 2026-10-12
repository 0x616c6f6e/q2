# Linux / WSL 构建

Linux 可以交叉编译 ESP32-S3 固件，也可构建可移植 Kernel 测试。
Linux 也可运行 [SDL2 x86 图形模拟器](linux-x86.md)：`python3 q2.py run --target x86`。
此目标无需激活 ESP-IDF，默认配置为 q2.linux.json；以下章节说明 ESP 构建。
四个独立仓库需完整存在：q2、app、kernel、platform；构建不会自动克隆子仓库。

当前硬件配置待确认：sdkconfig.defaults 已设为 8 MB Flash，但 partitions.csv 仍为 15 MiB
应用分区，完整字体固件约 10 MiB，默认构建会在分区检查失败。这与 Linux 工具链无关。
本次完整交叉编译用独立 `build/linux/esp32s3-reference16` 的 16 MB 配置验证，没有覆盖
8 MB 默认值。若实物为 8 MB，必须缩减字体并调整分区后再构建，不能直接烧录该参考固件。

## 使用现有 WSL SDK

本机 SDK 位于 `~/github/esp-idf`。在 **Ubuntu / WSL Bash** 中执行：

```bash
source ~/github/esp-idf/export.sh
cd ~/github/q2
bash build.sh
```

默认目标 esp32s3，配置 q2.esp32s3.json，固件位于
`build/linux/esp32s3/q2_kernel_esp32s3.bin`。此命令只构建，不烧录。
工程可移到 Linux 文件系统以改善 WSL 文件访问速度；不应复制旧构建缓存。

等效 Python 入口及常用选项：

```bash
python3 q2.py build --target esp32s3
bash build.sh --config q2.esp32s3.json --build-dir /tmp/q2-s3-build
python3 q2.py configure --target esp32s3
```

`build.sh` 接受 q2.py 的构建参数；可从任意工作目录运行，脚本会定位 q2.py。
相对 `--config` / `--build-dir` 路径仍相对调用者的当前目录，repositories 配置始终相对 q2 根目录。
默认使用激活环境的 python3，也可指定 `Q2_PYTHON=/path/to/python bash build.sh`。
Python 需 3.10+ 且安装当前 ESP-IDF 要求的依赖；优先使用 SDK 自己的虚拟环境。

## 新 Linux 环境准备

Ubuntu / Debian 所需基础软件可按 Espressif 文档安装，例如：

```bash
sudo apt-get update
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv \
    cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 build-essential
```

安装与项目兼容的 ESP-IDF 后，用该版本提供的安装器安装 ESP32-S3 工具链和 Python 依赖。
项目目前使用 ESP-IDF 6.2 开发版，不保证任意旧 SDK 都能编译。已有完整 SDK checkout 且提供
install.sh 时可执行：

```bash
bash ~/github/esp-idf/install.sh esp32s3
source ~/github/esp-idf/export.sh
```

新版 SDK 推荐的安装方式参见 [Espressif Linux 安装说明](https://github.com/espressif/esp-idf/blob/master/docs/en/get-started/linux-setup.rst)。
如果安装时自定义 `IDF_TOOLS_PATH`，激活时也必须使用同一个值。
不要在 Linux 使用 Windows 的 `.exe` 工具链或 `Scripts/python.exe`；WSL 需要 Linux 版本的工具。
入口不会自动修改 SDK、安装系统软件或永久修改 Shell 环境。

## 构建目录与 menuconfig

| 环境 | ESP32-S3 默认目录 |
|---|---|
| Windows PowerShell | build/esp32s3 |
| Linux / WSL | build/linux/esp32s3 |

Linux 其他目标同样输出到 `build/linux/<target>`，显式 `--build-dir` 则使用给定目录。
不要让两个系统共享同一个构建目录。SDK 路径发生变化时，根入口仍会备份不兼容缓存并保留
sdkconfig；详见 [缓存说明](development.md#esp-idf-构建缓存)。

首次 configure/build 后，从 q2 根目录调整 Linux SDK 配置：

```bash
idf.py -C platform/esp32s3 -B "$PWD/build/linux/esp32s3" \
    -D "SDKCONFIG=$PWD/build/linux/esp32s3/sdkconfig" menuconfig
bash build.sh
```

屏幕分辨率仍在 q2.esp32s3.json；Flash/PSRAM 等 SDK 参数在 sdkconfig。
Linux 初次构建不会继承 Windows 的 menuconfig 修改，需要自行核对硬件参数。

## 验证

```bash
bash -n build.sh
python3 scripts/test_linux_entry.py
python3 scripts/test_esp_build_cache.py
python3 scripts/test_project_config.py
python3 kernel/scripts/check_contracts.py
# 可选：使用 Linux GCC 构建和执行可移植 Kernel / APP 工具测试
python3 q2.py test --target kernel --compiler gcc
```

构建失败会透传非零退出码；不要只检查 bin 是否存在，因为它可能来自上一次成功构建。

本次环境与结果见 [Linux 验证记录](validation/linux-build.md)。
