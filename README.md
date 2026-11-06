# 2026CIE：跳水队 · 香山昆明湖V2 vdot

本项目在香山昆明湖V2（`KunminghuV2Config`）上实现自定义 `vdot.vv` 指令，完成环境验证、向量指令流程分析、Chisel硬件接入、基础测试、NEMU协同仿真和RVV基线性能评估。

当前硬件采用 **四级流水、VFEX0单套vdot功能单元**：两个128位向量源各取低8字节，计算8项signed int8点积，32位结果写入向量目的寄存器低32位，高96位清零。128次点积的完整程序实测为RVV **6378周期**、vdot **4797周期**，端到端加速比 **1.3296×**，周期减少 **24.79%**。

## 1. 三阶段文档与视频

三份汇总文档集中放在 `doc/`。讲解视频保存在本地 `videos/`，不纳入Git仓库；文件清单与交付说明见 [videos/README.md](videos/README.md)。

| 阶段 | 汇总文档 | 操作说明 | 讲解视频 |
|---|---|---|---|
| 第一阶段：部署、hello与向量加法 | [执行日志与操作文档](doc/第一阶段执行日志与操作文档.md) | [stage1 README](stage1/README.md) | `stage1.mp4`（官网单独提交） |
| 第二阶段：vdot硬件与基础测试 | [设计与基础测试文档](doc/第二阶段设计与基础测试文档.md) | [stage2 README](stage2/README.md) | `stage2.mp4`（官网单独提交） |
| 第三阶段：差分、波形与性能 | [协同仿真与性能分析文档](doc/第三阶段协同仿真与性能分析文档.md) | [stage3 README](stage3/README.md) | `stage3.mp4`（官网单独提交） |

### 赛题材料索引

| 要求 | 源码与材料入口 |
|---|---|
| 第一阶段环境及hello | [hello源码](stage1/hello/hello.c)、[运行日志](stage1/logs/)、[第一阶段报告](doc/第一阶段执行日志与操作文档.md) |
| 第一阶段向量加法流程 | [程序源码](stage1/vector-add/00_vl4_ta.S)、[八阶段截图](stage1/images/vector-add-vl4/) |
| 2.1 vdot设计 | [完整设计说明](stage2/2.1_design/vdot.vv设计说明.md) |
| 2.2 RTL实现 | [代码结构](stage2/2.2_rtl/README.md)、[Chisel源码](stage2/2.2_rtl/src/)、[功能补丁](stage2/2.2_rtl/xiangshan-vdot.patch) |
| 2.3 基础测试 | [测试材料](stage2/2.3_tests/README.md)、[正数](stage2/2.3_tests/2.3.1_positive/README.md)、[负数](stage2/2.3_tests/2.3.2_negative/README.md)、[边界](stage2/2.3_tests/2.3.3_boundary/README.md) |
| 3.1.1 NEMU扩展 | [源码结构](stage3/3.1.1_NEMU/README.md)、[接入说明](stage3/3.1.1_NEMU/接入说明.md)、[NEMU补丁](stage3/3.1.1_NEMU/vdot-nemu.patch) |
| 3.1.2 协同仿真 | [验证报告](stage3/3.1.2_协同仿真/验证报告.md)、[测试源码](stage3/3.1.2_协同仿真/programs/) |
| 3.2 RVV基线 | [程序结构](stage3/3.2_RVV基线/README.md)、[组合指令说明](stage3/3.2_RVV基线/基线说明.md) |
| 3.3 性能分析 | [实验分析报告](stage3/3.3_延迟分析/实验分析报告.md) |
| 第三阶段波形截图 | [5张截图与说明](stage3/images/README.md)、[文档中的逐图解读](doc/第三阶段协同仿真与性能分析文档.md#6-实际波形与延迟含义) |

## 2. 工程结构

```text
父目录/
├── xs-env/                            完整香山开发环境
└── cie2026-跳水-xiangshan-vdot/
    ├── README.md                      工程总览与导航
    ├── versions.json                  上游版本清单
    ├── doc/                           三阶段汇总报告
    ├── scripts/                       源码准备、NEMU构建、测试及波形审计
    ├── patches/build-compat.patch      构建兼容补丁
    ├── stage1/
    │   ├── hello/                     指定字符串程序
    │   ├── vector-add/                向量加法程序与运行脚本
    │   └── images/                    向量加法八阶段截图
    ├── stage2/
    │   ├── 2.1_design/                指令与微架构设计
    │   ├── 2.2_rtl/                   Chisel源码、补丁与局部测试
    │   ├── 2.3_tests/                 正数、负数、边界测试源码
    ├── stage3/
    │   ├── 3.1.1_NEMU/                参考模型与配置
    │   ├── 3.1.2_协同仿真/             整核测试程序与验证报告
    │   ├── 3.2_RVV基线/               等价性与性能程序
    │   ├── 3.3_延迟分析/              实验分析报告.md
    │   ├── hardware/                 与stage2一致的源码材料副本
    │   └── images/                   输入、乘法及三层加法截图
    ├── videos/                       视频交付说明；本地MP4已忽略
    ├── build/                        本地构建产物
    └── results/                      脚本生成的本地运行结果
```

`build/`、`results/`及本地复现目录按Git忽略规则管理。Git提交内容保留stage1日志，以及各阶段源码、测试程序、报告和截图；讲解视频单独提交，不随Git仓库分发；stage2、stage3的原始日志、复现目录、镜像和VCD不提交，按命令重新生成。文档中的结果是已完成实测的汇总。

## 3. 环境设置与版本

需要Linux、Git、Make、Python3、GCC/G++、RISC-V GNU工具链（默认 `riscv64-linux-gnu-`），以及xs-env所需的Java、Mill、Verilator与依赖库。完整上游版本见[versions.json](versions.json)。

| 仓库 | stage2、stage3复现基线 |
|---|---|
| xs-env | `8d9c5c2f6037da069818fd99ddee84d96dcea754` |
| XiangShan | `16ae9ddcda54fc9a2fddffad73174cf793ac7814` |
| NEMU | `af9d4ce51fc2087156b09f26d64a8e1cfb83332f` |

在新终端先设置路径；迁移机器时修改 `PROJECT`，环境不在同级时另行指定 `XS_ENV_ROOT`：

```bash
export PROJECT="$HOME/risc-v-compitition-26/cie2026-跳水-xiangshan-vdot"
export XS_ENV_ROOT="$(dirname "$PROJECT")/xs-env"
export EMU="$XS_ENV_ROOT/XiangShan/build/emu"
cd "$PROJECT"
```

若尚未准备xs-env，在不存在的目标目录初始化以下固定基线；已有匹配环境则跳过本段：

```bash
git clone https://github.com/OpenXiangShan/xs-env.git "$XS_ENV_ROOT"
git -C "$XS_ENV_ROOT" checkout 8d9c5c2f6037da069818fd99ddee84d96dcea754
git -C "$XS_ENV_ROOT" submodule update --init XiangShan NEMU
git -C "$XS_ENV_ROOT" submodule update --init --recursive DRAMsim3 nexus-am
git -C "$XS_ENV_ROOT/XiangShan" checkout 16ae9ddcda54fc9a2fddffad73174cf793ac7814
git -C "$XS_ENV_ROOT/NEMU" checkout af9d4ce51fc2087156b09f26d64a8e1cfb83332f
```



## 4. 第一阶段：hello与向量加法

已有可用的昆明湖V2 emu后执行。若从空环境复现当前扩展，可先完成第5节的源码接入和整核编译，再运行本节。

```bash
cd "$PROJECT"
source "$XS_ENV_ROOT/env.sh"
export EMU="$XS_ENV_ROOT/XiangShan/build/emu"
bash stage1/run-hello.sh
WAVE=1 BEGIN=0 END=5000 bash stage1/vector-add/run.sh 00_vl4_ta
```

指定hello输出为：

```text
hello xiangshan, I am lzw-super, IP SZU.
```

hello记录保存在 `stage1/logs/`，向量加法记录保存在 `stage1/vector-add/runs/`。两项均为 `--no-diff`。部署日志、八阶段执行过程及截图见[第一阶段报告](doc/第一阶段执行日志与操作文档.md)。

## 5. 第二阶段：硬件接入与基础测试

准备脚本应用vdot功能及构建兼容补丁，核验8个硬件文件和2个测试文件，并补齐固定版本chisel-template与其余依赖。整核emu由使用者手动编译：

```bash
cd "$PROJECT"
bash scripts/prepare-stage2.sh
source "$XS_ENV_ROOT/env.sh"
cd "$XS_ENV_ROOT/XiangShan"
make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j30
cd "$PROJECT"
export EMU="$XS_ENV_ROOT/XiangShan/build/emu"
bash stage2/2.3_tests/run.sh 00_smoke
bash stage2/2.3_tests/run.sh 01_directed
# 可选：导出冒烟波形
WAVE=1 BEGIN=0 END=12000 bash stage2/2.3_tests/run.sh 00_smoke
```

`EMU`必须显式设置为已包含vdot扩展的仿真器。`00_smoke`含1个正数样本，`01_directed`含10个定向样本，覆盖负数、混合符号、零、极值及源高位干扰；全部检查完整128位结果。脚本运行 `--no-diff`，新证据输出到 `stage2/2.3_tests/runs/`。

已构建对应emu时可直接设置路径后运行两项测试。镜像构建或 `make verify`通过仅表示构建/一致性检查成功，真正执行emu的是 `run.sh`。完整说明见[stage2 README](stage2/README.md)。

## 6. 第三阶段：NEMU、DiffTest与性能

复用stage2硬件和emu，准备NEMU扩展、记录本机emu身份，再构建参考库和运行全部测试：

```bash
cd "$PROJECT"
source "$XS_ENV_ROOT/env.sh"
python3 scripts/prepare.py --apply
python3 scripts/capture-emu.py
JOBS=12 bash scripts/build-nemu.sh
python3 scripts/run.py --all --wave
python3 scripts/report.py
```

参考库输出到 `build/nemu/`，模型检查包含1100组合法样本和7种非法配置。`--all`实际运行8项功能、1项RVV等价性和6项性能程序，共15项，全部显式开启 `--diff`，并使用同一 `boot.bin`。`--wave`只为00_smoke导出VCD。

新批次记录写入 `results/runs/<时间>/`：每项有实际镜像、汇编、命令、`result.json`及完整 `emu.log.gz`；`report.py`校验同一批日志和镜像后生成 `性能报告.md`。通过要求退出码0、出现 `Difftest enabled.`和 `HIT GOOD TRAP`，没有BAD TRAP/ABORT。

可提取冒烟波形中的握手、标签及四级算术信号：

```bash
RUN_DIR=$(python3 -c 'import json; print(json.load(open("results/latest.json"))["run"])')
python3 scripts/audit-vdot-vcd.py "$RUN_DIR/00_smoke/wave.vcd" \
  --output "$RUN_DIR/00_smoke/wave-audit"
```

输出 `selected.vcd`、事务CSV及审计摘要。已有5张截图位于 [stage3/images](stage3/images/README.md)，输入及8→4→2→1计算解读见[第三阶段文档第6节](doc/第三阶段协同仿真与性能分析文档.md#6-实际波形与延迟含义)。其他单项、基线与波形入口见[stage3 README](stage3/README.md)。

## 7. 已验证结果与审阅

2026-11-04已完成基础测试及全部15项整核DiffTest。NEMU模型1100组合法、7种非法配置通过；局部RTL测试2/2通过，流水检查1078笔输出。第三阶段新冒烟波形确认4核心周期FU延迟，完整性能配对如下：

| 点积次数 | RVV周期 | vdot周期 | RVV/vdot | 周期减少 |
|---:|---:|---:|---:|---:|
| 1 | 4571 | 4549 | 1.0048× | 0.48% |
| 32 | 5034 | 4653 | 1.0819× | 7.57% |
| 128 | 6378 | 4797 | 1.3296× | 24.79% |

这里比较完整裸机程序的核心周期，包含启动、配置、循环及自检，不将其等同于单条FU延迟或真实应用加速比。设计、数据来源与适用范围见[实验分析报告](stage3/3.3_延迟分析/实验分析报告.md)。

仅审阅提交材料时，无需安装xs-env，可在工程根目录运行：

```bash
python3 scripts/verify-package.py
```

该脚本仅核验RTL/NEMU源码快照、基线与11个基础测试参考样本，不依赖stage2、stage3原始日志。实际测试请按上面的命令运行并检查新日志。

源码保留上游许可：[XiangShan许可证](stage2/2.2_rtl/LICENSE.XiangShan)、[NEMU许可证](stage3/3.1.1_NEMU/LICENSE.NEMU)。
