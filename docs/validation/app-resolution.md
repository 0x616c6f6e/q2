# APP 分辨率适配验证

2026-10-10，在 WSL `/home/alon/github/q2` 修改；Windows Zig 0.13 运行原生资源加载测试。

- `python3 app/scripts/test_apps.py`：268 项通过，包括全部出厂 APP 可重复打包、尺寸目录打包/释放、旧 manifest、新字段非法值和创建模板。
- `python3 kernel/scripts/check_contracts.py`：38 portable files、92 documented APIs、69 component methods、1274 vendor checksums，通过。
- `ctest --test-dir build/linux/font-validation --output-on-failure`：8/8 通过，含 manifest C 解析、Lua/LVGL 实际调用、状态栏与整屏尺寸区别、APP 管理等。
- `platform/x86/test_assets.c` + 生产 `assets.c`：Windows 原生执行，71 项通过；验证当前尺寸覆盖、默认资源回退、仅加载当前尺寸、catalog UUID/别名、目录缺失、无效路径、损坏/超限文件及错误目录类型。测试注册器记录内容标记；PNG 解码由 Kernel 真实 LVGL 测试负责。
- `build/resolution-support/ui_matrix.c`：链接实际 Kernel/Lua/LVGL，执行已修改的 UI Demo；368×448、448×368、410×502、502×410 各自启用/关闭状态栏，共 8 种配置启动和渲染调用通过。

未做全部 APP 页面的视觉验收、ESP32 上板或完整固件重新构建；ESP32 内嵌 Demo 尚未实现 APP 目录图片加载。尺寸目录先复用原图标，不代表新增了四套不同设计画稿。
