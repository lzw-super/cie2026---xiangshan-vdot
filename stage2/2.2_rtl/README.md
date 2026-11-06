# 2.2 vdot.vv RTL实现

本目录包含8个硬件Chisel文件、2个局部测试及完整接入补丁。`src/`保留XiangShan原仓库路径，设计为8路有符号乘法与平衡加法树、四级流水、128位向量写回。

## 代码结构

```text
src/
├── main/scala/xiangshan/
│   ├── Parameters.scala                   VFEX0功能单元配置
│   └── backend/
│       ├── decode/
│       │   ├── Instructions.scala         自定义指令编码
│       │   ├── VecDecoder.scala           向量译码与操作数类型
│       │   └── DecodeUnit.scala           指令合法性检查
│       └── fu/
│           ├── FuType.scala               vdot功能类型
│           ├── FuConfig.scala             固定延迟与写回能力声明
│           ├── vector/VDotDataModule.scala 乘法、加法树及流水寄存器
│           └── wrapper/VDot.scala         控制、标签、异常与冲刷适配
└── test/scala/xiangshan/backend/fu/vector/
    ├── VDotTest.scala                     算术、流水及冲刷测试
    └── VDotDecodeTest.scala               编码与译码测试
```

## 配套文件

| 文件 | 内容 |
|---|---|
| [xiangshan-vdot.patch](xiangshan-vdot.patch) | 基于原始香山源码的完整功能补丁 |
| [base-commit.txt](base-commit.txt) | 接入所需的XiangShan基线版本 |
| [hardware-files.txt](hardware-files.txt) | 8个硬件源码路径 |
| [source.sha256](source.sha256) | 8个硬件文件与2个测试文件的校验和 |
| [LICENSE.XiangShan](LICENSE.XiangShan) | 上游源码许可证 |

设计细节见[设计说明](../2.1_design/vdot.vv设计说明.md)，环境准备、源码接入及运行步骤统一见[stage2 README](../README.md)。
