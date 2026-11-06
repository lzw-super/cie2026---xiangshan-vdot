# 第二阶段：vdot.vv设计与基础测试

基于香山昆明湖V2（`KunminghuV2Config`），实现四级流水、单套vdot功能单元。指令计算两个源寄存器低8字节的有符号int8点积，将32位结果写入向量目的寄存器低32位，高96位清零。

## 提交材料

| 要求 | 材料 |
|---|---|
| 2.1 设计文档 | [指令语义、编码与微架构](2.1_design/vdot.vv设计说明.md) |
| 2.2 RTL实现 | [Chisel源码与接入补丁](2.2_rtl/README.md) |
| 2.3.1 正数测试 | [正数点积报告](2.3_tests/2.3.1_positive/README.md) |
| 2.3.2 负数测试 | [负数点积报告](2.3_tests/2.3.2_negative/README.md) |
| 2.3.3 边界测试 | [零、极值及混合符号报告](2.3_tests/2.3.3_boundary/README.md) |
| 设计与测试汇总 | [第二阶段汇总文档](../doc/第二阶段设计与基础测试文档.md) |

## 1. 环境与源码准备

提交工程与完整 `xs-env` 放在同一父目录。依赖包括Git、Make、Python3、RISC-V GNU工具链（`riscv64-linux-gnu-`）及xs-env所需的Java、Mill、Verilator等构建工具。

```text
stage2/
├── README.md                      设计、接入和测试入口
├── SHA256SUMS                     提交文件校验和
├── 2.1_design/                    完整设计说明
├── 2.2_rtl/                       Chisel源码、补丁及局部测试
└── 2.3_tests/
    ├── 2.3.1_positive/            正数样本与结果说明
    ├── 2.3.2_negative/            负数样本与结果说明
    ├── 2.3.3_boundary/            边界样本与结果说明
    ├── suites/*/source/           必需的汇编、公共代码、JSON及链接脚本
    ├── images.sha256              已验证镜像的参考哈希
    ├── Makefile                   镜像构建与哈希核对
    └── run.sh                     整核测试入口
```

源码基线：xs-env为 `8d9c5c2f6037da069818fd99ddee84d96dcea754`，XiangShan为 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`。以下命令针对已准备的匹配基线；从零获取xs-env的步骤见[工程根README](../README.md)：

```bash
export PROJECT="$HOME/risc-v-compitition-26/cie2026-跳水-xiangshan-vdot"
export XS_ENV_ROOT="$(dirname "$PROJECT")/xs-env"
cd "$PROJECT"
bash scripts/prepare-stage2.sh
```

[prepare-stage2.sh](../scripts/prepare-stage2.sh)自动应用功能及构建兼容补丁、核验10个源码文件、补齐固定版本chisel-template、初始化依赖并校验测试镜像。已完整接入时会检查并跳过补丁；基线不符或存在未接入的本地修改时停止。

源码快照保留原XiangShan路径，位于 `stage2/2.2_rtl/src/`；上述脚本通过补丁完成同等源码接入，无需手动逐文件替换。第二阶段采用 `--no-diff` 自检，NEMU协同验证见stage3。

## 2. 编译emu

```bash
source "$XS_ENV_ROOT/env.sh"
cd "$XS_ENV_ROOT/XiangShan"
make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j30
export EMU="$XS_ENV_ROOT/XiangShan/build/emu"
cd "$PROJECT"
```

必须使用接入vdot后编译的emu。若已有对应构建产物，可直接设置 `EMU` 后执行测试。

## 3. 运行基础测试与导出波形

```bash
cd "$PROJECT"
export EMU="$XS_ENV_ROOT/XiangShan/build/emu"
bash stage2/2.3_tests/run.sh 00_smoke
bash stage2/2.3_tests/run.sh 01_directed
# 可选：导出冒烟波形
WAVE=1 BEGIN=0 END=12000 bash stage2/2.3_tests/run.sh 00_smoke
```

`00_smoke`验证正数点积，`01_directed`包含10组负数、混合符号、零及极值样本。程序比较完整128位结果，包含高96位清零检查。

脚本自动重建并核对镜像，每次结果保存在 `stage2/2.3_tests/runs/` 的独立目录，包含镜像、环境信息、`emu.log`及`result.txt`；启用波形时另生成 `wave.vcd`。退出码0、出现 `HIT GOOD TRAP` 且无 `HIT BAD TRAP` 即判定通过，终端打印 `PASS`。

## 4. 验证结果

2026-11-04重新构建emu后的整核复现全部通过，周期与既有实测汇总一致：

| 套件 | 点积样本数 | 提交指令数 | 整程序周期 | 结果 |
|---|---:|---:|---:|---|
| 00_smoke | 1 | 166 | 4515 | PASS |
| 01_directed | 10 | 1507 | 7501 | PASS |

局部RTL测试 `VDotTest`、`VDotDecodeTest` 均通过，流水测试检查1078笔输出。整程序周期包含启动、配置和自检；四级功能单元延迟为4核心周期。


