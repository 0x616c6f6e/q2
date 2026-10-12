# 项目配置

产品配置来自根目录 JSON：Windows 默认 `q2.json`，Linux x86 默认 `q2.linux.json`，
ESP32-S3 默认 `q2.esp32s3.json`；每次构建只读取所选的一份配置。`q2.py` 与根 CMake 都会校验字段、类型、范围和依赖；未知字段和重复 JSON 属性拒绝。切换配置使用 `--config <file>`，不会合并旧配置。所有 repositories 相对路径始终相对 q2 根目录。

生成结果保存在 `build/<target>/generated/`：q2_project_config.h、project.cmake、resolved.json。不要手动编辑；相同内容不会重写时间戳。CMake 监听 JSON 与生成器的变动，`cmake --build` 也会重新配置。Platform 通过显式 Q2_GENERATED_DIR 消费生成头；Kernel 不读产品头/JSON。

Linux / WSL 根入口默认改用 `build/linux/<target>/generated/`，隔离 Windows 的绝对路径缓存。
`--build-dir` 可显式覆盖；安装和构建方法见 [Linux 构建](linux-build.md)。

## 配置字段

| 字段 | 默认 / 规则 |
|---|---|
| format | 1，配置格式版本 |
| repositories.app/kernel/platform | 三个独立 checkout 路径 |
| display.width / height | 502 / 410，整数 64–1024 |
| display.brightness | 整数百分比 0–100；ESP32-S3 启动亮度，当前 AM178 配置为 100（寄存器 0xFF）；其他后端未实现物理亮度控制。旧配置缺字段保留 100 |
| display.rotation | 0、90、180、270（整数度数）；非零目前仅 ESP32-S3 AM178/AM213 实现；见平台旋转表 |
| display.cjk_font | true；编译霞鹜文楷中文回退字库及 Tiny TTF；false 仅保留 Montserrat 英文、数字和图标 |
| system_ui.status_bar / screensaver | true / true；系统状态栏、屏保分别控制 |
| system_ui.status_bar_height | 32；24–64，至少留下 32 像素 APP 区域 |
| system_ui.idle_timeout_ms | 30000；1000–3600000 ms |
| system_ui.clock_move_interval_ms | 10000；1000–3600000 ms |
| system_ui.lock_enabled | false；开启锁屏需 keys 组件 |
| system_ui.status_left / status_right | {time} / {wifi} {bt} {ble} {battery}；最多 127 UTF-8 字节 |
| system_ui.saver_text | {time}；同样支持状态模板 |
| system_ui.unlock_key / unlock_action | POWER / 2（双击）；键名须存在，动作 1/2/3 |
| keys.names | POWER、BACK、PREV、NEXT、PLAY；1–32 个独立名称 |
| keys.single_min_ms | 20；有效短按下限，不是立即上报单击的时间 |
| keys.double_gap_ms | 300；第一次松开至第二次按下的间隔，恰好等于阈值按两个单击处理 |
| keys.long_press_ms | 800；达到时上报一次 LONG，必须大于 single_min_ms |
| logging.enabled | true；控制 Q2_ENABLE_LOG，关闭不会隐藏致命 CLI 错误 |
| logging.level | info；off/error/warn/info/debug |
| web.enabled / port | true / 8765；仅 x86 本机硬件模拟，0 为自动端口 |
| app.startup | homepage；APP 目录名，UUID 仍由 APP manifest 管理 |
| app.grants | 产品允许的能力列表；仍须与 manifest/READY 后端求交集 |

按键时间单位均为 ms，范围 1–60000。单击等待双击窗口后确认，长按只报一次，Kernel 只透传动作。按键名称和阈值既进入二进制，也由 Web 状态接口显示。

系统 UI 行为、输入过滤及 APP 可用尺寸见 [状态栏与屏保](system-ui.md)。旧配置没有 system_ui 段时默认关闭这两项，已有字段仍严格校验；新增 lifecycle 字段在旧配置中缺失时补默认值。Settings 保存的偏好覆盖 JSON 出厂值，详情见系统 UI 文档。

## 组件开关的实际含义

| components 字段 | x86 | host | ESP32-S31 最小入口 |
|---|---|---|---|
| display | 必须开启，LVGL 图形 provider | 可开关文本显示注册 | 尚无屏幕后端，必须关闭 |
| storage | LittleFS 文件后端，关闭不编译/挂载存储 | LittleFS RAM，关闭不分配介质 | 必须关闭，未注册实物设备 |
| keys | 可开关命名按键注册 | 未接入，必须关闭 | 未接入，必须关闭 |
| apps | 可开关多 VM/常驻 Home 管理；关闭改为单 APP | 单 APP，必须关闭 | 未启动产品 APP，必须关闭 |
| sqlite | 可选内存数据库，不持久保存 | 同左 | 未接入，必须关闭 |
| usb | 无真实 DCD，拒绝开启 | 同左 | 尚无 DCD，拒绝开启 |
| network | 可开关 WinHTTP HTTP/HTTPS 注册 | 未接入，必须关闭 | 未接入，必须关闭 |
| audio | Windows MP3/WAV 默认设备播放 | 未实现，拒绝开启 | 仅注册接口/模拟后端测试 |
| wireless | 尚未实现，拒绝开启 | 同左 | 同左 |

display/apps/keys 的 provider 注册按配置控制，Kernel 的通用注册/API 源码仍保留，不通过大面积条件编译修改公共协议。storage/sqlite/LVGL 库的编译由对应公开 CMake 开关控制。关闭 apps 后请选择 settings、ui-demo 或 device-info 等单 APP；homepage 需要 apps 能力，启动会被拒绝。关闭 keys 时必须同时关闭 web；key-demo 的 required input.keys 也会阻止它启动。

`--target kernel` 是组件/契约构建，不启动产品 provider。此目标允许 USB 库；同时打开 storage/sqlite/usb 时启用带 fake DCD 的完整集成测试。fake DCD 仅用于测试，不表示平台 USB 可用。

## 使用其他目标

要试 host，将 components.network/data/keys/apps、web.enabled、system_ui.status_bar/screensaver 设为 false，选择 app.startup=device-info。display/storage/sqlite 可以自行开关：

```sh
python q2.py run --target host --config q2.local.json --compiler zig
```

ESP32-S31 目前要求所有 components、web.enabled、system_ui.status_bar/screensaver 为 false，配置仍可设置日志、未来屏幕尺寸等产品参数。在已激活且支持 ESP32-S31 的 ESP-IDF 环境执行：

```sh
python q2.py build --target esp32s31 --config q2.local.json
```

默认生成到根 build/esp32s31，sdkconfig 也在该目录；不会烧录。ESP 产品外设接入后，应补充实现、能力校验和硬件测试再放开对应开关。

## 独立 Platform 使用

独立仓库可直接 `cmake -S x86 ... -DQ2_KERNEL_DIR=<kernel>`，此时 common/q2_platform_config.h 提供可独立编译的默认值；这不是第二份产品配置。可通过明确传入 Q2_GENERATED_DIR 使用其他产品生成的头。Kernel 及 APP 独立工具不需要 q2 根目录。

components.data：x86 默认开启通用状态/事件注册。关闭时 APP 可查询 data.read 并降级；host/ESP 最小入口未接入，须关闭。新增配置在旧文件中按目标补默认值。领域能力包括 power.read、wireless.read、clock.read，均还需 data.read；详见 [设备数据](device-data.md)。

components.network：根产品默认 true；旧配置缺字段补 false。控制 provider 注册，不自动发起请求；APP 仍需 network.http 授权。仅 x86 有实际网络后端，不代表 wireless 已实现。

### ESP32-S3 AM178 profile

`--target esp32s3` 默认读取根 `q2.esp32s3.json`（可用 --config 显式替换）。
当前要求 display/apps=true，其他硬件组件和 Web 关闭；startup=homepage，嵌入 factory.json 中的出厂应用。授权列表在产品 JSON 中配置，并与每个 manifest 取交集。system_ui 可用，默认状态栏开启、屏保/锁屏关闭。实体按键未接入，主页支持触摸，设置仅会话生效。
分辨率只允许 368×448 / 448×368；不允许让未实现的外设配置为可用。
SDK Flash/PSRAM 配置仍属于 Platform 的 sdkconfig，产品 JSON 不复制 SDK 选项。


## 中文字体编译开关

在当前目标使用的配置里修改 `display.cjk_font`：
PC 使用 `q2.json`，ESP32-S3 默认使用 `q2.esp32s3.json`。

```json
"display": {
  "width": 368,
  "height": 448,
  "cjk_font": false
}
```

上例是 ESP32-S3 配置；PC 请保留其原有宽高。修改后重新构建：

```sh
source ~/github/esp-idf/export.sh
bash build.sh
```

这是编译开关，运行中的 APP 不能切换；无需手动删除缓存。
true 保留中文歌名，false 不生成/链接大字库，且不编译 Tiny TTF 渲染实现。
关闭后中文显示为缺字占位；英文、数字、基础图标仍可用。
它与 Music 的歌词开关独立，不改变歌词设置。旧配置缺少该字段时默认 true。

产品生成器将此值传给公共 CMake 选项 `Q2_ENABLE_CJK_FONT`。
独立 Kernel / x86 / ESP32-S3 构建可传 `-DQ2_ENABLE_CJK_FONT=OFF`；
通过 q2 根入口构建时以 JSON 为准，不在 menuconfig 维护第二份配置。

### ESP32-S3 屏幕型号

`display.panel` 可选 `am178` 或 `am213`；其他目标为 `generic`。旧 ESP32-S3 配置默认 am178。
AM213 使用 410×502（0/180 度）或 502×410（90/270 度），尺寸不匹配会被拒绝。
参考根配置 `q2.esp32s3-am213.json` 和 [AM213 接入说明](../platform/esp32s3/docs/am213.md)。
