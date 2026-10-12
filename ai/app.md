# Q2-App AI 开发指南

先读 [APP README](../app/README.md)、[APP 协议](../app/docs/app-contract.md)、[Lua API](../kernel/docs/lua-api.md) 和 [能力清单](../kernel/ai/capabilities.json)。只使用已经实现的 API，不凭名称推测 `q.wifi`、`q.audio` 存在。`q.ui` 仅在注册 LVGL provider 后存在，并且需要 display.ui 授权。

- Lua 四空格，主逻辑拆到 src/，视图和业务分离；关键降级和状态转换写逻辑注释。
- 新应用只在创建时生成 UUID，已有应用升级保持 ID，按 SemVer 更新版本。
- 权限精确声明，optional 需要拒绝路径；不扩大权限来绕过测试。
- UI 坐标从 q.ui.width/height 推导，不能假设竖屏高度 502。图片仅使用已注册的 assets/name.png；管理模式下背景通过 appearance API 共享并保存；独立调试仍使用 settings 私有键 background。
- Q2-App 不修改 Kernel 或板级 SDK；新系统能力先设计独立契约。
- 出厂角色由 factory.json 指定，不能写进 APP manifest；应用目录与导航契约见 [homepage](../app/docs/homepage.md)。
- 执行 validate、test_apps、pack，再用目标 host runner 验证真实 Lua 逻辑。
- 交付说明包路径、目标 API、必需/可选权限与未验证硬件行为。

可复用任务：为 API 2 创建 <应用>，保留 UUID、申请最少能力、处理拒绝，使用已实现的方法，提供独立 Lua 源码/manifest/资源、确定性包与实际运行记录。

Homepage 采用单应用横向切换，不再绘制纵向列表。使用 q.ui.label 的可选 align 实现文字居中，q.ui.image 的可选 size 实现等比例图标；不要通过估算字符宽度伪造居中。修改导航后同步 test_homepage_ui.py 的真实点击与首尾切换覆盖。

系统状态栏启用时 q.ui.height() 已扣除它的高度，不要再次减去 32。APP 坐标从内容区原点开始；注入物理点击的测试需增加状态栏偏移。屏保期间 APP 不重启，唤醒动作不会送给 APP。详情见 [系统 UI](../docs/system-ui.md)。

多 VM 协作：on_tick(now_ms) 不等于线程，按截止时间限流；隐藏 APP 继续执行。home 保留实例，exit 结束。处理 ui.resize 重新布局但保留业务状态；自己的 ui.clear 不影响其他实例。screensaver.inhibit 仅清醒前台可续期，permission_denied 是正常后台/锁屏分支，不能 assert 或循环重试。修改相关行为运行 test_lifecycle_ui.py。系统 UI 策略只在 Homepage shell.lua，普通 APP 不获得系统层权限。

设备状态优先使用 q.data.get/subscribe，声明 data.read 及 key 的领域权限。检查 value ~= nil，避免误判 0/false；失效通知使用 event.valid/status。get 不触发采样，事件没有历史读取。通用 API 与示例见 kernel/docs/data.md；Key Demo 提供前台按键订阅例子。

Music 的 `audio.playback` 通过平台注册异步后端；网络 URL 播放还需 `network.http`。
先 `audio.open()`，分片 `audio.write()`，再 `audio.play()`；每次调用遵守 255 字节参数限制。
APP 应轮询实际 state/position/duration，不用计时器伪造播放进度；跨 APP 所有权和退出清理见 kernel/docs/audio.md。

### 分辨率适配

APP manifest 的 supported_resolutions 是 1–16 个唯一 WIDTHxHEIGHT 字符串（各轴64–1024）；它是适配元数据，不作启动拦截。q.ui.resolution() 返回完整逻辑屏幕字符串；q.ui.width()/height() 是内容区。x86 资源变体位于 assets/<resolution>/，代码保持平铺 key；参见 docs/app-resolution.md。修改布局需处理未知尺寸及 ui.resize；不要把状态栏高度扣除后的尺寸当作设备分辨率。
