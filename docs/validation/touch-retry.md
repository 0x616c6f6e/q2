# AM178 间歇性触摸 NACK 修复验证

2026-10-10。用户确认按钮可以触发，但偶尔失灵。

当前 ESP-IDF i2c_master.c 的同步失败路径将 NACK 映射为 ESP_ERR_INVALID_RESPONSE。
原驱动单次失败便清除 cached pressed，owner 立即向 LVGL 发松手，放大了偶发通信故障的影响。
厂商参考的 0x2E 地址、0xE0 三字节报文和组合事务保持不变；不关闭 ACK 检查。

修改：INT 开始读取，IO/timeout 最多三次尝试、间隔至少 5 ms；每轮至多读一次，不阻塞等待。
等待重试时保持最后有效状态；新 IRQ 不重置重试预算；耗尽后释放并返回错误。
owner 取消额外 20 ms 读取门限，仍每轮延时 10 ms；空闲无 IRQ/待重试时不会访问 I2C。
新增首次有效报文、重试恢复与耗尽诊断，恢复/耗尽日志限流 5 秒并累计计数。
保留用户当前板级内部上拉设置，纠正文档与实现不一致的描述。

验证：
- tests/test_touch.c：23 项通过，覆盖空闲、瞬态 IO、timeout、释放报文重试、
  新 IRQ 不刷新预算、耗尽释放、后续 IRQ 恢复和参数错误。
- kernel/scripts/check_contracts.py：通过。
- source ~/github/esp-idf/export.sh 后 bash build.sh：成功。
- build/linux/esp32s3 的 build.ninja 包含 am178_touch.c；ELF 中确认存在首次报文、
  touch retry recovered 和 touch read exhausted 诊断字符串；固件 0x984d0 字节。

未烧录或测量 SDA/SCL/INT。此改动修复错误处理缺陷，并不能证明供电/上拉/排线或 TP 固件的 NACK 根因已消除。
刷入后观察三色按钮、持续按住/移动/松开、重试恢复计数及是否仍有三次耗尽日志。
