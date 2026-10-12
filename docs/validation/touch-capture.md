# AM178 快速点击采集修复

2026-10-10。用户报告连续快速点击丢失；代码发现 TP 报文读取和 QSPI 同步刷新共用 owner，
单个中断标记只保存待读状态，不能保存刷屏期间每次按下/松手的报告。

修改位于 platform/esp32s3/main/am178.c、am178.h、main.c：
- 独立 FreeRTOS q2_touch 采集任务（priority 5 / 4096-byte stack），INT 唤醒，保留原有有界重试。
- 32 项实际样本 FIFO；移动可降采样，边沿有预留空间；满队列报告 stalls 并保序等待。
- owner 每批最多回放 16 个样本，仅 owner 调用 Kernel/Lua/LVGL；队列空不生成松手。
- 停止时禁用 ISR、通知任务、等待读取停止，再回收队列/I²C。
- 新日志 down/up/queued/stalls 用于区分采集丢失和 UI 积压。

验证：
- Kernel CTest 8/8 通过。test_lvgl.c 新增真实 Lua/LVGL 32 次点击批量回放，全部计数成功。
- platform/esp32s3/tests/test_touch.c 原 23 项重试测试通过。
- kernel/scripts/check_contracts.py 通过。
- 激活 ~/github/esp-idf/export.sh 后 bash build.sh 成功，输出 build/linux/esp32s3/q2_kernel_esp32s3.bin。

未烧录测试，也未测量 TP/INT/SDA/SCL。本次修复了明确的软件采集阻塞风险；不能保证
控制器尚未读出的中间报告、连续 I²C 故障或队列满时的触摸仍然完整。刷入后检查快速点击、
长按/拖动/松手，以及诊断 stalls 是否为 0，并对照采集计数与 UI Touches 计数。
