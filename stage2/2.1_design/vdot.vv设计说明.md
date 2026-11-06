# vdot.vv 指令设计说明

对应提交要求2.1。目标平台为香山昆明湖V2，配置 `KunminghuV2Config`，XiangShan基线 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`。本文说明已实现、已进行整核功能测试的固定八项有符号字节点积扩展。

## 1. 指令语义

指令记法为 `vdot.vv vd, vs1, vs2`。两个源和目的均为128位向量寄存器；输出虽是一个32位标量数值，存放位置仍是向量目的寄存器，而非整数rd。

| 属性 | 本实现定义 |
|---|---|
| VLEN | 128位 |
| 支持的执行配置 | SEW=8、LMUL=m1、VL=8、vstart=0、vm=1 |
| 输入元素 | 各源低64位的8个int8，byte i对应bits[8i+7:8i] |
| 运算 | 8项有符号乘积求和，不累加旧vd |
| 结果 | 精确和符号扩展为32位，写入vd[31:0] |
| 高位 | vd[127:32]恒为0，负数结果也不做128位符号扩展 |
| 高64位输入 | 完全不参与计算 |
| 掩码/尾部策略 | 算术不做mask/tail/old-vd合并，完整覆盖目的128位 |

参考伪代码：

```python
s = 0
for i in range(8):
    a = (vs1 >> (8*i)) & 0xff
    b = (vs2 >> (8*i)) & 0xff
    a = a - 256 if a >= 128 else a
    b = b - 256 if b >= 128 else b
    s += a * b
vd = s & 0xffffffff  # 128位容器中，其余96位全部为0
```

例如：和为36，整个目的为 `0x00000000000000000000000000000024`；和为-8，整个目的为 `0x000000000000000000000000fffffff8`。

实现不包含通用动态SEW/LMUL点积、masked dot、旧目的累加或任意vstart重启。装载和结果检查允许使用VL=16，真正执行vdot时切回VL=8。源/目的重叠、源相同以及v0作为源/目的已有整核测试。

## 2. 指令编码与译码

采用项目自定义OP-V编码，不宣称为标准RISC-V已分配编码。

| 位段 | 定义 |
|---|---|
| [31:26] | funct6=111111 |
| [25] | vm=1 |
| [24:20] | vs2 |
| [19:15] | vs1 |
| [14:12] | funct3=000 |
| [11:7] | vd |
| [6:0] | opcode=1010111（0x57） |

```text
BitPat = b1111111??????????000?????1010111
match  = 0xfe000057
mask   = 0xfe00707f
word   = match | (vs2 << 20) | (vs1 << 15) | (vd << 7)
vdot.vv v3,v1,v2 = 0xfe2081d7
```

测试使用VDOT汇编宏产生机器码，无需修改GNU汇编器。未扩展助记符的objdump可能显示原始word。

`Instructions.scala`定义匹配模式；`VecDecoder.scala`通过OPIVV表项选择新 `FuType.vdot`。设置向量写回、不设置整数写回，`src3=SrcType.no`消除旧vd寄存器依赖。vm固定为1，无掩码源依赖；保留vconfig源，等待正确的实际VL配置。

非e8/m1、非法vtype、非零vstart在译码置非法指令；FU还按对齐的输出控制检查VL=8、vm及其余配置。vm=0不匹配新指令，落入非法指令。VL=7、e16、m2、vstart=1及vm=0已有整核负向测试；其他不支持配置不列为已测覆盖。

## 3. 微架构与香山后端接入

```text
取指/译码（OP-V，自定义FuType.vdot）
  → m1单uop拆分 → 向量重命名、源依赖与物理目的分配
  → 向量调度队列 → OG2/读操作数/旁路
  → VFEX0中的独立VDot FU（四级）
  → 既有向量/V0写回路径 → ROB完成与架构提交
```

`FuType.vdot`追加在既有枚举末尾，不改变原类型索引，并加入向量算术分类。`FuConfig`将其声明为piped、固定延迟4、128位目的、支持向量/V0写口，纳入向量控制、OG2及通用功能单元配置列表。

`Parameters.scala`仅向VFEX0增加VdotCfg，复用该执行单元现有寄存器读写资源。固定延迟声明使通用调度、唤醒及写回预约逻辑知道新FU的时间关系；原VialuCfg/VimacCfg延迟未改。SEW8/m1下沿用VEC_VVV拆分契约，产生一个uop。

保留与现有向量FU兼容的五个数据槽位：vs1、vs2、oldvd占位、v0占位、vconfig。oldvd与mask数据不进入算术，译码也不等待其寄存器依赖；vconfig仍用于VL与配置对齐。

## 4. 四级数据通路

算术源码为[VDotDataModule.scala](../2.2_rtl/src/main/scala/xiangshan/backend/fu/vector/VDotDataModule.scala)，适配包装为[VDot.scala](../2.2_rtl/src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala)。

| 阶段 | 组合运算 | 寄存器 |
|---|---|---|
| S1 | 8路并行signed int8×int8 | 8×SInt(16.W) products |
| S2 | 相邻两乘积相加 | 4×SInt(17.W) sums2 |
| S3 | 相邻两部分和相加 | 2×SInt(18.W) sums4 |
| S4 | 两个四项和相加 | 1×SInt(19.W) sum8 |

```text
vs1[63:0] ─┐
            ├→ 8乘法 → S1 → 4加法 → S2 → 2加法 → S3 → 1加法 → S4
vs2[63:0] ─┘                                                 │
                       vd[127:0] ← Cat(96'b0, signExtend32(sum8))
```

所有字节先 `.asSInt`；加法使用 `+&` 保留增长位。八项精确结果范围为[-130048,131072]，19位有符号数可容纳；18位有符号正数上限只有131071，不能容纳全-128乘全-128的结果。最终19→32位符号扩展后拼接96个0，不增加第五级寄存器。

模块绕过普通向量的Mgu合并逻辑，因此tu/mu、ta/ma均不导致旧vd或尾部内容保留。没有使用旧vd累加，也不修改YunSuan的通用乘加模块。

## 5. 控制、标签与冲刷

包装器继承 `VecPipedFuncUnit` 和 `HasPipelineReg`，算术四级enable连接每一级 `regEnable`；robIdx、pdest、写使能和向量控制从ExeUnit共享控制流水取同周期结果，不能只延迟数据而遗漏目的标签。

ExeUnit的共享valid流水处理redirect取消，包装器还屏蔽输出当拍需要flush的结果。无效事务可在算术寄存器留下旧数据，但不应产生有效结果交付。对于已经发生的推测写回，最终依靠既有ROB/重命名恢复保证错误路径不架构提交。

该接口沿用香山固定延迟管线和写回预约，不承诺任意ready反压下的弹性队列行为。局部测试在输出ready恒为true条件下验证连续、bubble、不同标签、四阶段取消和复位。

## 6. 实测验证与边界

已完成局部RTL及整核实测，结果汇总如下。提交保留源码、测试程序、设计报告和截图，不包含stage2原始日志、镜像或VCD；复现操作见[stage2 README](../README.md)。

- 两项局部RTL测试通过：288种译码寄存器组合；流水实际检查1078笔输出，覆盖定向/随机、气泡、v0、标签、逐阶段取消与复位。
- 基础整核套件00_smoke与01_directed通过，分别覆盖1个正数样本与10个定向样本；全部比较完整128位结果，使用no-diff自检。
- 既有流水测量核对54笔输入/输出和810次算术寄存器更新，FU延迟4核心周期；16条独立指令连续逐拍发射。
- RAW链相邻输入间隔实测9周期，与4周期FU延迟不同。
- 扩展的随机、重叠、分支及非法配置整核DiffTest见[第三阶段](../../stage3/README.md)。

## 7. 实现文件与复现

提交的[RTL目录](../2.2_rtl/README.md)包含8个硬件源码文件、2个Scala测试、完整接入补丁及基线版本。保持原XiangShan目录结构，便于审查与恢复；Chisel源码需在对应完整仓库中编译，不是孤立scala脚本。

原环境构建命令：

```bash
cd xs-env
source ./env.sh
cd XiangShan
make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j30
```

新基线恢复方式和局部测试命令见[stage2 README](../README.md)；赛题三类测试入口和复现命令见[测试说明](../2.3_tests/README.md)。
