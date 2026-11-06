# 2.3 基础测试材料

本目录包含正数、负数和边界值测试说明，以及可重新构建的测试源码与参考数据。测试使用香山KunminghuV2 emu，以 `--no-diff` 方式自检完整128位结果，包括高96位清零。

## 测试实例与结果

| 赛题要求 | 实例与期望结果 | 套件及说明 |
|---|---|---|
| 2.3.1 正数 | [1…8]与全1点积为36 | 00_smoke；[正数报告](2.3.1_positive/README.md) |
| 2.3.2 负数 | 全1与全−1点积为−8；另含混合符号 | 01_directed；[负数报告](2.3.2_negative/README.md) |
| 2.3.3 边界 | 全0得0；全127相乘得129032；全−128相乘得131072；全−128与全127得−130048 | 01_directed；[边界报告](2.3.3_boundary/README.md) |

| 套件 | 样本数 | 提交指令数 | 整程序周期 | 结果 |
|---|---:|---:|---:|---|
| 00_smoke | 1 | 166 | 4515 | PASS |
| 01_directed | 10 | 1507 | 7501 | PASS |

2026-11-04整核复现通过，周期与文档实测汇总一致。负数和边界分类共用01_directed的同一次运行；整程序周期包含启动、配置及自检开销。

## 文件结构与本地结果位置

```text
2.3_tests/
├── 2.3.1_positive/README.md      正数样本及结果说明
├── 2.3.2_negative/README.md      负数样本及结果说明
├── 2.3.3_boundary/README.md      边界样本及结果说明
├── suites/
│   ├── 00_smoke/source/         正数测试汇编、JSON、common.S及link.ld
│   └── 01_directed/source/      10个定向样本及公共源码
├── images.sha256                已验证镜像的参考哈希
├── Makefile                    测试镜像构建与一致性校验
├── run.sh                      基础整核测试入口
├── build/                      本地重新构建的镜像
└── runs/                       本地复现日志与可选wave.vcd
```


新运行结果位于 `runs/` 的独立子目录，包含 `result.txt`、`emu.log`和`environment.log`，启用波形时另有 `wave.vcd`。通过条件为退出码0、出现 `HIT GOOD TRAP`且无 `HIT BAD TRAP`。

所有构建、测试与波形导出命令统一见[stage2 README](../README.md)。

提交不包含原始日志及已编译镜像，也不依赖旧artifacts目录；构建后按images.sha256核对新镜像。报告中的PASS与周期为已完成实测的汇总，新环境应以自己生成的日志为准。
