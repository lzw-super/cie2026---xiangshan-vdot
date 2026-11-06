# 第三阶段波形截图

本目录用于保存用户提供的5张原始波形截图，顺序为输入、并行乘法、三层加法。截图对应00_smoke的八项正数点积。


| 原图顺序 | 保存文件名 | 画面 | 关键读数 |
|---|---|---|---|
| 1 | [01-vdot-input-vs1-vs2.png](01-vdot-input-vs1-vs2.png) | 输入vs1/vs2及握手 | 低8字节分别为1～8和全1；ROB 0x19、pdest 0x35 |
| 2 | [02-vdot-products.png](02-vdot-products.png) | S1八路乘法 | products_0～7为0x0001～0x0008 |
| 3 | [03-vdot-sums2.png](03-vdot-sums2.png) | S2第一层加法 | sums2为0x00003、0x00007、0x0000b、0x0000f |
| 4 | [04-vdot-sums4.png](04-vdot-sums4.png) | S3第二层加法 | sums4为0x0000a、0x0001a |
| 5 | [05-vdot-sum8.png](05-vdot-sum8.png) | S4最终加法 | sum8为0x00024，即十进制36 |

逐图解读已补充到 [第三阶段协同仿真与性能分析文档](../../doc/第三阶段协同仿真与性能分析文档.md)的第6节。所有截图读数按十六进制解释。
