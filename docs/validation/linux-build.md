# Linux 构建验证

环境：WSL Ubuntu，Python 3.12.3、CMake 3.28.3、Ninja、系统 GCC。
使用用户现有 `/home/alon/github/esp-idf`，版本描述
`v6.1-dev-7447-g2067f3ae32b`，SDK 自报 6.2；Xtensa GCC 16.1.0（esp-16.1.0_20260609）。

## 已通过

- Bash 语法检查；4 项入口测试（宿主缓存隔离、自定义目录、带空格的解释器/参数、错误码）。
- Linux 下 4 项 ESP 缓存测试和 10 项产品配置测试。
- `python3 q2.py test --target kernel --compiler gcc`：实际原生构建，12/12 CTest、
  175 项 APP 工具检查、Kernel 契约检查全部通过。
- Windows 入口回归：2 项目录测试通过，2 项 Linux Bash 测试按设计跳过。
- `bash build.sh --build-dir build/linux/esp32s3-reference16` 完整交叉编译通过，
  bootloader、分区表与 q2_kernel_esp32s3.bin 均生成，分区容量检查通过。

## 限制

默认 Flash 已被设为 8 MB，而现有分区及字体仍按 16 MB 设计。默认 Linux 构建实测在
分区检查失败。因此完整交叉编译另用生成目录内的 16 MB 配置完成，未修改产品默认值。
这证明 Linux 构建链和源码可编译，不代表 8 MB 固件已经适配；实际 Flash 容量仍待确认。
未烧录硬件，未迁移 Windows x86 图形模拟器到 Linux。

最初启动的临时 Linux SDK 工具安装已停止，后续全部验证使用用户指定 SDK。
本地日志位于 build/linux-kernel-test.log、build/linux-esp32s3.log、
build/linux-esp32s3-reference16.log；它们与生成固件均不提交。
