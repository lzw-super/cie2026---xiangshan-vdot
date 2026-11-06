# 2.3.1 正数点积测试

状态：**香山KunminghuV2整核自检PASS**，退出码0，HIT GOOD TRAP；运行方式为no-diff。

| 样本ID | vs1低8个有符号字节 | vs2低8个有符号字节 | 期望十进制 | vd[31:0] |
|---|---|---|---:|---|
| 1 | [1, 2, 3, 4, 5, 6, 7, 8] | [1, 1, 1, 1, 1, 1, 1, 1] | 36 | `0x00000024` |

以上每个结果的vd[127:32]均必须为0；程序逐字节检查全部16字节。

整个套件：166条指令、4515周期，ROB记录1条vdot提交。周期数包含启动及自检开销，不是单条vdot延迟。

- [汇编源码](../suites/00_smoke/source/00_smoke.S)
- [公共完整结果检查](../suites/00_smoke/source/common.S)
- [参考输入/结果](../suites/00_smoke/source/00_smoke.json)

复现操作见[stage2 README](../../README.md)。在工程根目录设置EMU后运行对应套件；新的result.txt、emu.log和environment.log位于2.3_tests/runs的独立时间目录。

本分类保留测试源码、输入与期望值及实测结果汇总；stage2原始日志和镜像不随包提交，需运行脚本重新生成。
