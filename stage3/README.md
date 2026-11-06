# 第三阶段：协同仿真、RVV基线与性能分析

基于当前stage2的四级流水、单套vdot硬件，扩展NEMU参考模型，完成真实DiffTest、已有RVV指令组合基线与端到端周期加速分析。

## 提交材料与结构

```text
stage3/
├── README.md                      本阶段复现入口
├── 3.1.1_NEMU/
│   ├── source/                    NEMU修改源码快照
│   ├── vdot-nemu.patch             指令扩展及平台适配补丁
│   ├── base-commit.txt             NEMU固定基线
│   ├── ref.config、boot.bin        参考配置及统一启动镜像
│   └── tests/                     独立模型验证程序
├── 3.1.2_协同仿真/
│   ├── programs/                  8组整核功能测试及构建文件
│   └── 验证报告.md                覆盖范围与验收结果
├── 3.2_RVV基线/                   等价性、6个性能配对程序及生成器
├── 3.3_延迟分析/                  当前设计实验分析报告
├── hardware/                     与stage2一致的硬件源码副本
└── images/                       5张实际波形截图
```

| 要求 | 说明 |
|---|---|
| 3.1.1 NEMU指令扩展 | [源码结构](3.1.1_NEMU/README.md)、[接入说明](3.1.1_NEMU/接入说明.md) |
| 3.1.2 协同仿真 | [测试材料结构](3.1.2_协同仿真/README.md)、[验证报告](3.1.2_协同仿真/验证报告.md) |
| 3.2 RVV组合基线 | [程序结构](3.2_RVV基线/README.md)、[基线说明](3.2_RVV基线/基线说明.md) |
| 3.3 延迟加速分析 | [当前设计实验分析报告](3.3_延迟分析/实验分析报告.md) |
| 三阶段汇总 | [第三阶段协同仿真与性能分析](../doc/第三阶段协同仿真与性能分析文档.md) |

## 1. 环境和NEMU接入

复用[stage2](../stage2/README.md)已接入并构建的KunminghuV2 emu，无需重复应用hardware中的补丁。环境与提交工程同级，NEMU扩展基于 `af9d4ce51fc2087156b09f26d64a8e1cfb83332f`。

```bash
export PROJECT="$HOME/risc-v-compitition-26/cie2026-跳水-xiangshan-vdot"
export XS_ENV_ROOT="$(realpath "$PROJECT/../xs-env")"
cd "$PROJECT"
source "$XS_ENV_ROOT/env.sh"
python3 scripts/prepare.py --apply
python3 scripts/capture-emu.py
```

`prepare.py`检查stage2硬件并应用NEMU补丁，已接入时校验后跳过。基线不匹配时停止；脚本不切换或重置版本。`capture-emu.py`核验当前构建与源码并记录新emu身份。

## 2. 构建参考库与模型测试

```bash
cd "$PROJECT"
JOBS=12 bash scripts/build-nemu.sh
```

脚本选择昆明湖V2专用参考配置，生成 `build/nemu/riscv64-nemu-interpreter-so`，并实际执行1100组合法及7种非法配置的模型测试。通过后输出 `PASS: actual NEMU model`。模型检查完整128位结果，覆盖寄存器重叠及非法配置；NEMU只提供功能参考，不模拟流水时序。

## 3. 整核协同仿真与性能汇总

```bash
cd "$PROJECT"
python3 scripts/run.py --all --wave
python3 scripts/report.py
```

`--all`依次运行8组功能套件、1组RVV等价性测试及6个性能配对程序，共15项。每项显式开启 `--diff` 并使用相同 `boot.bin`；退出码0、日志包含 `Difftest enabled.` 与 `HIT GOOD TRAP`、无BAD TRAP/ABORT才通过。

`--wave`只为00_smoke导出VCD，不为随机和性能套件生成大波形；不需要波形时省略该选项。完成全套运行后，可提取关键信号并核对流水：

```bash
RUN_DIR=$(python3 -c 'import json; print(json.load(open("results/latest.json"))["run"])')
python3 scripts/audit-vdot-vcd.py "$RUN_DIR/00_smoke/wave.vcd" \
  --output "$RUN_DIR/00_smoke/wave-audit"
```

输出 `selected.vcd`、事务CSV和摘要，检查算术、目的标签与4周期FU延迟。若仅复现某一项，可使用：

```bash
python3 scripts/run.py --case 01_directed
python3 scripts/run.py --baseline
```

`--baseline`执行RVV等价性和6个性能配对程序，共7项。参考库与RTL始终共同执行实际指令，没有跳过vdot差分。

本地运行写入 `results/runs/<时间>/`，包含每项镜像、汇编、命令、完整压缩日志与结果JSON；`report.py`校验当次日志后输出 `性能报告.md`。

## 4. 结果与测量口径

最新复现结果与证据位置见[协同仿真报告](3.1.2_协同仿真/验证报告.md)和[性能分析报告](3.3_延迟分析/实验分析报告.md)。性能取RTL的整程序 `cycleCnt`，比较RVV组合与vdot在相同启动、输入、循环和自检条件下的周期，计算 `C_RVV/C_vdot`。它包括公共开销，与单条功能单元的4周期执行延迟属于不同测量口径。


2026-11-04实际复现：NEMU模型1100＋7通过、整核DiffTest **15/15通过**。128次点积RVV为6378周期，vdot为4797周期，端到端加速比 **1.3296×**。
