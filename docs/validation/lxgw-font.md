# LXGW WenKai Lite 字体移植验证

工作区：WSL /home/alon/github/q2；上游版本 v1.522，提交
067a6d508532cc0f8bc79e899ec3b06ff4dee38a。

## 修改

- 中文回退资源替换为霞鹜文楷 Lite Regular，20/40px 继续使用 Tiny TTF。
- 保留上游全部 25,598 个 Unicode cmap 映射，包含非 BMP 字符；去除不用的排版/hint 数据。
- 来源、OFL 许可证、哈希和重制工具同步更新；旧资源备份在 build/font-import/previous。
- Montserrat 英文/数字/图标和 Music 的 lyrics_enabled=false 保持原配置。

## 验证结果

- 固定 fonttools 4.60.1 重复生成，字体二进制逐字节相同。
- 新字体与上游 Unicode cmap 集合完全相同；可打印 ASCII、简繁 UI、粤语和标点样本无缺字。
- Linux GCC / 真实 LVGL：q2_lvgl_contracts、q2_system_ui_contracts，2/2 通过。
  覆盖实际字体链的简繁、粤语和 U+20BB7 字形，检查不是缺字占位。
- kernel/scripts/check_contracts.py 通过（38 个可移植文件、91 个公开 API、
  68 个组件方法、1274 个上游文件校验）。
- 激活 ~/github/esp-idf/export.sh 后执行 bash build.sh，ESP32-S3 编译成功，无烧录。

## 实测尺寸

| 项目 | 大小 |
|---|---:|
| 原字体资源 | 9,900,208 字节 |
| 新字体资源 | 13,462,252 字节（12.84 MiB） |
| 编译前已有 S3 固件 | 10,536,736 字节 |
| 新 S3 固件 | 14,098,816 字节（13.45 MiB） |
| 应用分区 | 15,728,640 字节（15 MiB） |
| 剩余应用分区 | 1,629,824 字节（1.55 MiB） |

字体覆盖以该上游版本为限，例如 U+3400 不包含；没有无限字符覆盖或网络补字功能。
当前参考硬件配置为 16 MB Flash；后续业务增长仍需重新检查分区。
本次未验证实物屏幕观感、真实账户或音频设备；宿主测试不等同于实机验证。
