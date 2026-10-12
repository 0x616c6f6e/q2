# 字体编译开关验证

产品配置 `display.cjk_font` 映射到 `Q2_ENABLE_CJK_FONT`，缺省 true。
false 时不生成/链接 CJK 字库，并关闭 Tiny TTF；保留 Montserrat 英文、数字及图标。
此开关与 Music 歌词设置独立。

- 配置测试 11/11、Linux 入口测试 4/4、Kernel 契约检查通过。
- 同一 Linux 宿主构建目录 OFF → ON，两种状态的 LVGL / system UI 测试各 2/2 通过。
- OFF 验证英文、数字、播放图标和无中文 fallback；ON 验证简繁、粤语及非 BMP 字形。
- ESP32-S3 两种配置交叉编译通过；ELF 确认 CJK 数组及 Tiny TTF 构造函数仅在 ON 时存在。
- OFF 固件 621,632 字节（607.1 KiB）；ON 固件 14,098,816 字节（13.45 MiB）。

测试目录为 build/linux/font-validation、build/linux/esp32s3-font-off、
build/linux/esp32s3-font-on；临时配置与日志在 build/font-switch/。
当前产品 PC 配置为 true，ESP32-S3 配置为 false。
编译期间触摸源码曾出现重复声明，当前源码恢复后重试通过；本任务没有修改触摸实现。
未烧录，未实机验证。
