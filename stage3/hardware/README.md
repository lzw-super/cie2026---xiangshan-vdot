# 2.2 vdot.vv RTL实现

提交语言：**Chisel**，满足“Verilog/Chisel代码”要求；不另附整颗CPU生成的巨量Verilog。

本目录的 `src/` 是已通过测试的真实源码快照，不是伪代码。目录层次与XiangShan仓库一致。核心功能单元：

- [VDotDataModule.scala](src/main/scala/xiangshan/backend/fu/vector/VDotDataModule.scala)：8路signed乘法、平衡加法树、四级寄存器、全128位结果。
- [VDot.scala](src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala)：控制流水、标签、异常及redirect接入。

其余6个硬件文件负责自定义指令模式、译码、FuType、FuConfig与VFEX0配置；两项测试位于 `src/test/scala/xiangshan/backend/fu/vector/`。

## 接入现有香山

基线commit见[base-commit.txt](base-commit.txt)。在**匹配基线、尚未加入本扩展**的完整XiangShan仓库执行（先设置实际绝对路径）：

```bash
SUBMISSION=/absolute/path/to/submission
# 当前目录为XiangShan仓库
 git apply --check "$SUBMISSION/2.2_rtl/xiangshan-vdot.patch"
 git apply "$SUBMISSION/2.2_rtl/xiangshan-vdot.patch"
 sha256sum -c "$SUBMISSION/2.2_rtl/source.sha256"
 mill -i xiangshan.test.testOnly \
   xiangshan.backend.fu.vector.VDotTest \
   xiangshan.backend.fu.vector.VDotDecodeTest
 make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j30
```

本目录与当前stage2硬件一致。复现按工程根README构建KunminghuV2Config，并记录仿真器身份。既有依赖（rocket-chip、YunSuan等）来自完整xs-env，未复制到提交包。`source.sha256`覆盖8个硬件文件与2个Scala测试，可在本目录直接运行 `sha256sum -c source.sha256` 核验快照。

没有修改NEMU模型；整核验证使用no-diff。源码继承原仓库内容，其许可证随附于[LICENSE.XiangShan](LICENSE.XiangShan)，保留已有源码声明。
