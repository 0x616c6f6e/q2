# 开发规范

## 风格与注释

内部诊断使用 `q2/log.h` 的 Q2_LOGE/W/I/D，避免在 Kernel 绑定 printf 或 SDK 日志。过滤参数不得包含业务副作用；日志 sink 失败不覆盖业务返回值。新增后端须同时验证编译关闭和运行 OFF，见 [日志规范](../kernel/docs/logging.md)。

- C11，UTF-8、LF、四空格、110 列，使用目录内 `.clang-format`；不格式化第三方源码。
- 公共类型使用 `q2_*_t`，函数使用 `q2_`，常量使用 `Q2_`。实现细节 static，跨模块只依赖公开契约。
- Python 3.10+，四空格、Black 110 列；Lua 四空格。路径使用平台独立接口，不写死开发者盘符。
- 公开 API 在头文件使用 Doxygen 注释，说明用途、生命周期/所有权、执行上下文、输入限制和错误行为。新增复杂参数时补充 `@param`/`@return`。
- 逻辑注释写明为什么验证、为什么如此排序、失败如何回滚，以及重要单位/边界，不逐行翻译代码。
- 所有 Q2 业务操作统一 `q2_result_t`，输出参数 `out_*`；明确检查错误，禁止用假成功掩盖未实现功能。
- 注册项、内存、DMA、事件、APP 资源必须明确所有者和释放路径。新增有状态 API 同时实现 `release_app`。

## 最小变更流程

1. 先确定修改属于 Kernel、SoC 还是 App；更新公开契约与能力清单。
2. 保持 SoC SDK 不进入 Kernel；APP 不读寄存器或使用原始 C 指针。
3. 写实现和关键逻辑注释；有错误分支就设计清理与重试行为。
4. 添加能发现实际回归的契约或集成测试，包含拒绝/故障路径。
5. 运行格式化、边界/依赖检查、宿主测试；修改移植接口后执行目标交叉编译。
6. 更新 Lua 文档、机器能力清单、验证记录。记录未实现和未实机验证的部分。

## 验证命令

产品验证在 q2 根目录执行 `python q2.py test`。下面的独立 Kernel 命令在 kernel 目录执行：

Linux 使用 `python3 q2.py test --target kernel --compiler gcc` 验证可移植部分；
ESP32-S3 交叉编译使用 `bash build.sh`，见 [Linux 构建](linux-build.md)。

```sh
python scripts/check_contracts.py
python scripts/build.py --cc clang
# 格式检查只传入 include/src/components/tests 下的第一方 .c/.h
clang-format --dry-run --Werror <files>
```

构建脚本的编译器可通过 `--cc` 或 Q2_CC 设置，Zig 可直接传可执行文件路径。UBSan 检查未定义行为，不等于全量内存泄漏、硬件或并发验证。CMake/CTest 另验证独立构建图。App 工具测试在 Q2-App 独立执行。

## 依赖和版本

### ESP-IDF 构建缓存

在已激活的 ESP-IDF 终端内，从 q2 根目录执行 `./build.ps1 -Target esp32s3`。
入口使用当前 `IDF_PATH` 和运行脚本的 Python；需要指定解释器时使用 `-Python <python.exe>`。
不要在同一构建目录同时启动多个构建。

切换 SDK、Python 或项目源目录时，主工程重新配置不一定会清除 bootloader 的独立 CMake 缓存。
`q2.py` 会分别检查这两层缓存和项目描述中的 SDK 路径；
Python 路径按 ESP-IDF 的比较规则处理，即使 `python` / `python3` 指向同一解释器，入口名称改变也需重建缓存；发现不匹配时，将整个旧构建目录
移至同级 `<目录名>.sdk-backup-<时间戳>`，复制保留 `sdkconfig` / `sdkconfig.old`，然后重新生成。
旧文件不会删除，新的固件仍输出到原构建目录。若原构建目录已被手动删除，则按平台
`sdkconfig.defaults` 生成配置，无法恢复已删除的自定义 menuconfig 设置。

看到 `CMake ... source ... does not match ... used to generate cache` 时，应通过根入口重试，
不要手改 CMakeCache.txt 内的路径。直接调用 `idf.py` 不会经过 Q2 的缓存检测。
此检测处理路径变化，不替代 SDK 升级时的配置迁移或不同目标之间的配置审查。

固定第三方版本和下载校验，更新时核对许可证、来源和文件锁；只修改必要配置，记录补丁。不能把厂商 SDK 的文件系统 wrapper 拷进 Kernel 来获得隐含平台依赖。

C ABI 与 Lua API 独立版本化。改变公共布局/语义先判断 ABI/API 是否需要升级，再同步文档和测试。现有第一方源码尚未选择发布许可证，不因第三方采用 MIT 就自动为整个项目声明 MIT。
