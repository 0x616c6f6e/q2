# Python 统一入口

所有命令从 q2 根目录通过 `python3 q2.py`（Windows 为 `python q2.py`）执行。
需要 Python 3.10+；配置管理只使用标准库，不需要安装 Python 包或激活 ESP-IDF。
`q2.py --help` 查看构建/运行选项，`q2.py config --help` 查看配置管理。
已有 `--target`、`--config`、Bash 和 PowerShell 调用继续兼容；`--platform` 是 `--target` 的别名。

## 平台和预设

```sh
python3 q2.py platforms
python3 q2.py config list
```

| --profile | 平台 | JSON 配置 | 默认构建目录（Linux） |
|---|---|---|---|
| x86-linux | x86 / SDL2 | q2.linux.json | build/linux/x86 |
| x86-windows | x86 / Windows 原生窗口 | q2.json | Windows 为 build/x86 |
| esp32s3-am178 | ESP32-S3 / AM178 | q2.esp32s3.json | build/linux/esp32s3 |
| esp32s3-am213 | ESP32-S3 / AM213 | q2.esp32s3-am213.json | build/linux/esp32s3-am213 |
| host | 文本宿主 / device-info | q2.host.json | build/linux/host |
| kernel | 内核契约测试（含 fake DCD） | q2.kernel.json | build/linux/kernel |
| esp32s31 | 最小移植入口 | q2.esp32s31.json | build/linux/esp32s31 |

不指定预设时默认当前操作系统的 x86；`--target esp32s3` 默认 AM178。
指定已知根配置文件时可自动识别平台，例如 `--config q2.esp32s3-am213.json`。
外部或 `q2.local.json` 文件不猜测芯片，使用 `--profile` 或 `--target` 明确选择；
指定 `--profile` 和 `--config` 时，JSON 以自定义文件为准，预设只选择平台。
`--target` 与 `--profile` 指向不同平台时会拒绝执行。

每次操作读取一份 JSON，不叠加多个配置源。不自动选择上次使用的配置。
AM178/AM213 缓存分开；自定义文件按绝对路径的摘要隔离缓存，同一文件改参数后增量构建。
Windows 与 Linux 缓存隔离；`--build-dir` 可覆盖，但使用者需避免并发操作同一构建目录。
所有配置中的 `repositories` 相对路径仍相对 q2 根目录。

## 配置管理

```sh
# 查看经过默认值补全的配置，不写文件
python3 q2.py config show --profile esp32s3-am213
python3 q2.py config validate --profile esp32s3-am213

# 从预设创建本地配置；默认输出根 q2.local.json，已有文件不会覆盖
python3 q2.py config init --profile esp32s3-am213

# 一次修改多个关联参数；新屏幕尺寸须与旋转角度匹配
python3 q2.py config set --profile esp32s3-am213 --config q2.local.json \
  display.rotation=0 display.width=410 display.height=502 display.brightness=80

# 布尔开关、按键时间也经过相同的平台能力校验
python3 q2.py config set --profile esp32s3-am213 --config q2.local.json display.cjk_font=false
python3 q2.py config set --profile x86-linux keys.double_gap_ms=350 keys.long_press_ms=900

# --output 创建新配置而非修改所选预设；不覆盖已有目标文件
python3 q2.py config set --profile x86-linux --output build/custom-pc.json logging.enabled=false
```

`set` 参数使用 `点分字段名=JSON值`，支持数值、布尔、字符串、数组和对象。
字符串必须保留 JSON 双引号，例如 Bash 中 `'logging.level="debug"'`；
不同 Windows Shell 的原生程序引号规则可能不同，可直接编辑 JSON 后使用 `config validate`。
重复字段赋值、未知字段、类型错误、非法范围和平台未实现能力都会失败。
多个字段全部通过校验才发布文件；失败保留原文件，临时文件自动回收。
`init` / `set --output` 不覆盖已有文件；`set` 未指定输出时更新当前所选源文件。
这些命令仅修改产品 JSON，ESP-IDF 专属设置仍通过 menuconfig 管理。

## 编译和运行

```sh
# Linux SDL2；默认 run 先配置并编译，再打包启动 APP
python3 q2.py build --profile x86-linux --compiler gcc
python3 q2.py run --profile x86-linux
python3 q2.py run --profile x86-linux --app key-demo
python3 q2.py run --profile x86-linux --headless --frames 30 --disable-web

# 无窗口宿主程序、内核契约测试
python3 q2.py run --profile host
python3 q2.py test --profile kernel --compiler gcc

# ESP32-S3 需要先激活当前 SDK；build 只构建，run 烧录后打开串口
source ~/github/esp-idf/export.sh
python q2.py build --profile esp32s3-am213
python q2.py menuconfig --profile esp32s3-am213
python q2.py run --profile esp32s3-am213 --port /dev/ttyUSB0
python q2.py flash --profile esp32s3-am213 --port /dev/ttyUSB0 --baud 460800
python q2.py monitor --profile esp32s3-am213 --port /dev/ttyUSB0 --monitor-baud 115200

# 使用自定义配置编译；后续 run / menuconfig 使用同一组 profile/config/build-dir
python q2.py build --profile esp32s3-am213 --config q2.local.json
```

ESP `run --flash-only` 仅烧录，`run --monitor-only` 仅监视；
串口可通过 `Q2_PORT` / `ESPPORT` 提供。ESP 的 `test` 未实现，使用 `--profile kernel` 做宿主测试。
`--jobs` 用于原生 CMake 编译；ESP-IDF 使用其自身并行策略。
Windows 可直接调用 Python，或 `./build.ps1 -Profile esp32s3-am213`、
`./run.ps1 -Profile esp32s3-am213 -Port COM3`。Windows 需要在 ESP-IDF 终端中操作 ESP。
不自动安装 SDK、不自动选择/打开串口；子工具失败后返回非零状态并停止后续步骤。

x86-linux 尚未实现音频；ESP32-S3 当前提供屏幕、触摸和出厂 APP，
ESP32-S31 仅最小移植入口，需要支持该芯片的 ESP-IDF，不能当作已实现的 MP3 产品固件。
`kernel` 是测试构建，不支持 `run`；fake USB DCD 不代表硬件 USB 已完成。

## 验证入口

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 q2.py test --profile x86-linux --compiler gcc
```

统一入口回归测试覆盖配置事务失败不写入、不同屏幕/自定义配置的缓存隔离、
平台选择冲突、已知配置识别、ESP 烧录/监视参数及失败停止。
构建结果、运行存储文件和 APP 打包结果仍在根 build / dist，不进入子仓库。
