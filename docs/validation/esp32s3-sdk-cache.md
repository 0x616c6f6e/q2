# ESP32-S3 SDK 缓存修复验证

日期：2026-10-09。仅构建验证，未烧录、未测试实机。

## 原因与修复

主工程已切换到新 ESP-IDF，而 bootloader/CMakeCache.txt 仍引用旧
firmware_old/.tools/idf-bt/components/bootloader/subproject，导致 CMake 源目录不匹配。
根入口现在分别检查主工程、bootloader 和 project_description.json；路径不匹配时
备份完整构建目录，保留 sdkconfig，再生成新缓存。

## 本次结果

- 实际使用用户当前 Desktop/github/esp-idf 与 idf6.2_py3.14_env，通过根 build.ps1 构建。
- 开始验证时旧 build 目录已不存在，因此本次实际构建使用 sdkconfig.defaults；
  旧配置保留行为由临时目录回归测试验证，没有声称恢复已删除的配置。
- 首次编译在 SDK esp_time_impl.c 处无诊断退出；相同环境重试成功，未修改 SDK 或关闭编译检查。
- bootloader、分区表和 q2_kernel_esp32s3.bin 均生成；应用大小 10,540,048 字节，
  15 MiB 应用分区剩余约 33%。Flash 配置为 16 MB，PSRAM 为 octal，仍需与实际硬件核对。
- 固件 SHA256：ae7c722281d49916142e38cda44a6497e9a4fdbc8b82fe7339647d9c6f5ca2f7。
- 4 项缓存回归测试、10 项产品配置测试通过；Kernel 契约检查通过。
- 完成后再次检查实际主工程/bootloader 缓存，确认兼容且不会重复备份。

本地详细日志：build/esp32s3-current-sdk.log 与 build/esp32s3-current-sdk-retry.log（忽略文件）。
