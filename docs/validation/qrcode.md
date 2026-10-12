# 二维码 APP 验证（2026-10-09）

用户已启用 LV_USE_QRCODE=1，本轮保留此设置，并增加 Lua UI 方法与固定文本 APP。未添加键盘/编辑器或更改第三方源码。

- Windows x86 构建通过；CTest 10/10 通过。
- 扩展 LVGL 测试验证二维码像素、静区、尺寸/边界、空内容拒绝、不允许拉伸、清屏后句柄失效及重复创建/清理。
- 真实 framebuffer 在 502×410、410×502、320×320 三种窗口尺寸由 ZXing 解出 Q2-Kernel。
- 临时测试内容含 URL、中文 UTF-8 和 255 字节文本，解码结果逐一与原文一致。
- Back 实际点击退出与 resident Home 中打开 QR Code 均通过；APP 已加入七应用目录。
- APP 工具 86 项通过；契约检查 34 portable files / 88 public APIs / 55 component methods / 1274 vendor checksums 通过。

[默认画面](../images/qrcode.png)。当前证据为 Windows 模拟器渲染及独立解码，不等于实物屏幕亮度/反光条件下的手机扫描测试。

在 q2 根目录执行：

```powershell
ctest --test-dir build/data --output-on-failure
python kernel/scripts/check_contracts.py
python app/scripts/test_apps.py
# 测试依赖 Pillow、zxing-cpp；生成码使用 LVGL，解码使用独立 ZXing
python app/scripts/test_qrcode_ui.py --runner build/data/bin/q2_x86.exe --artifacts build/qrcode-test/verified
```
