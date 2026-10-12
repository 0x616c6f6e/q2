# 平台适配开发

新增平台以独立目录存放入口、SDK 构建文件、设备驱动和板级配置。通过外部路径消费 Kernel，不复制其业务实现，不在 Kernel 加入芯片型号分支。

最小接入是内存分配、释放、单调时钟；最小组件是 ABI/size/id/start/stop。以 host/main.c 为完整生命周期参考，esp32s31/main/main.c 为 RTOS owner 入口参考。

所有 Q2 API 在唯一 owner 调用。ISR 和其他线程先投递到平台自己的线程安全队列，owner 取出后调用 q2_event_post；异步完成事件必须带对应 APP instance，防止已关闭应用收到延迟结果。不要把 SDK 错误直接透传，转换到 q2_result_t。

硬件参数放板级配置：Flash 分区、GPIO、I2C 地址、显示尺寸、DMA 缓冲、USB PHY。只在有实际实现并初始化成功时注册/报告能力。TinyUSB 的测试 DCD 不能用于实机。

从旧固件迁入时，先分离通用服务和驱动：例如解码/播放控制属于 Kernel audio 组件，I2S/DAC 引脚与 DMA 属于平台；Wi-Fi/BT SDK 调用属于平台，面向 APP 的权限、命令和状态协议属于 Kernel。

验收包括 host 契约测试、目标构建和硬件实测三种独立证据。编译通过不能替代 USB 枚举、SD 掉电、音频连续输出、无线共存或电源验证。AI 开发时记录使用的 SDK 版本、编译参数、固件大小和未验证项。

产品主页集成参考 x86/main.c、catalog.c 和 Kernel application-manager.md：注册可信 APP 目录，bind caller-owned resident runtime，在 owner 的 poll 之后 advance。通过 apps_state 更新 lvgl_focus/keys_route；先 apps_shutdown 再销毁 Home runtime。普通 APP VM 由 manager 管理。非锁屏的物理 Home 操作由生命周期判断后请求回主页，可信平台快捷导航可转成 q2_apps_request(NULL)，不要在 ISR 或 Lua 回调里直接替换 VM。ESP32-S3 已接入只读出厂目录和常驻主页；ESP32 / ESP32-S31 仍为最小入口；经典 ESP32 适配复制自 S31，使用独立 SDK 目标和默认 Flash/UART 参数。

按键接入使用 q2/keys.h：boot 前注册名称，SoC/驱动识别 SINGLE/DOUBLE/LONG 后从 owner 调用 q2_keys_report。不得将消抖/长按时间阈值塞入 Kernel。x86 的 web.c 接收原始按下/松开，由 key_input.c 在 owner 上使用单调时钟识别；阈值统一位于 q2/q2.json。Kernel 不依赖该配置。真实 ESP 按键识别尚未实现。

新增设备状态优先注册 q2_data_spec_t，通过 q2_data_publish 在 owner 上更新；中断/驱动线程只进入平台队列。以 x86/device_data.c 为例，未实现设备默认发布 unsupported；仅明确启用的 Web 调试模拟可发布用户输入，不能将它报告为实机采样。读取仅访问缓存；控制使用命令 API。component 的额外 capabilities 表用于让动态领域能力参与 manifest 授权，必须在 boot 前保持稳定。

## ESP32-S3 AM178

新增真实 Xtensa 目标：`platform/esp32s3`，SPI2 QSPI 像素后端与 I²C CHSC6417 触摸。
平台负责 RGB888→RGB565、软件旋转、偶数窗口扩展和同步传输；owner 转发触摸到通用 Display。
AM178/AM213 正式启动使用独立 Q2-App 的 Homepage/Settings；CMake 生成固件内置目录与当前分辨率资源，使用同一 Kernel APP manager。网络、音频和持久存储尚未迁移。
产品入口 `build.ps1 -Target esp32s3`；配置、连接表和未完成范围见平台 README。

ESP32-S3 AMOLED 使用 `q2_lvgl_full_refresh(display, true)`（boot 前）在 PSRAM 完成整帧合成，
同步后端再旋转、转 RGB565 并按原生行发送。PC 默认 32 行局部刷新；API 不暴露 LVGL/SDK 类型，
开启后需为 `width * height * 4` 绘图缓冲预留内存。失败保留原缓冲，运行期间拒绝切换模式。
整帧模式降低旋转局部窗口碎片，但不等于 TE 同步或硬件双缓冲；以实机确认残影和滚动效果。
