# 3.1.1 NEMU指令扩展材料

本目录实现与当前stage2硬件一致的vdot功能语义：8项有符号字节点积，写入向量目的低32位，高96位清零。

| 文件或目录 | 内容 |
|---|---|
| [source/](source/) | 按NEMU原路径保存的修改源码：指令注册、译码、点积执行、异常与参考配置 |
| [vdot-nemu.patch](vdot-nemu.patch) | 基于固定上游版本的完整接入补丁 |
| [base-commit.txt](base-commit.txt)、[source.sha256](source.sha256) | 基线版本及源码校验和 |
| [ref.config](ref.config) | 昆明湖V2的实际参考配置 |
| [boot.bin](boot.bin) | DUT与REF共同使用的启动镜像 |
| [tests/nemu_model_test.c](tests/nemu_model_test.c) | 1100组合法、7种非法配置的独立模型测试 |
| [接入说明.md](接入说明.md) | 编码、语义与平台异常适配说明 |
| [LICENSE.NEMU](LICENSE.NEMU) | 上游许可证 |

构建和运行命令统一见[stage3 README](../README.md)。实际参考库输出至工程根目录的 `build/nemu/`，模型验证日志随本次复现记录保存。
