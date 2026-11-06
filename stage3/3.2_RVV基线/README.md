# 3.2 RVV基线程序

使用已有RVV指令组合实现与vdot相同的完整128位结果，作为功能和性能对照。算法、寄存器约定及公平性说明见[基线说明](基线说明.md)。

| 文件或目录 | 内容 |
|---|---|
| [generate.py](generate.py) | RVV组合序列、42组等价性样本及性能程序生成 |
| [program.py](program.py) | 生成器使用的程序构建辅助逻辑 |
| [fixtures.json](fixtures.json) | 固定输入数据 |
| [common.S](common.S) | 启动、配置和完整结果自检 |
| [link.ld](link.ld)、[Makefile](Makefile) | 链接及7个程序的构建规则 |
| `build/` | 本地生成的汇编、bin/ELF、反汇编和符号表 |

生成程序为 `rvv_equivalence`，以及点积次数为1、32、128的 `bench_rvv_*`、`bench_vdot_*`。每一对采用相同输入和公共控制流程；RVV主体5条指令，vdot主体1条指令。

运行命令统一见[stage3 README](../README.md)，周期表与加速比见[当前设计实验分析报告](../3.3_延迟分析/实验分析报告.md)。原始日志与镜像不随包提交；复现后在本地results/runs查看新结果。
