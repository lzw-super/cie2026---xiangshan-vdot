# 第一阶段实验

[第一阶段执行日志与操作文档](../doc/第一阶段执行日志与操作文档.md)包含环境与构建记录、hello验证和向量加法的八阶段波形分析；[doc中的报告](../doc/第一阶段执行日志与操作文档.md)内容一致。


## 当前目录与运行约定

提交工程与 `xs-env` 位于同一父目录：

```text
risc-v-compitition-26/
├── xs-env/                          # 完整香山、NEMU和nexus-am环境
└── cie2026-跳水-xiangshan-vdot/       # 本提交工程，PROJECT
    ├── README.md
    ├── doc/                        # 本文及三阶段汇总
    ├── scripts/
    └── stage1/
        ├── hello/                  # 指定字符串程序
        ├── logs/                   # hello日志、镜像与配置记录
        ├── vector-add/             # 向量加法程序与runs/运行记录
        ├── images/vector-add-vl4/   # 13张波形截图
        └── reference/              # 供文档阅读的源码节选
```

当前布局为同一父目录下的 `xs-env/` 与 `cie2026-跳水-xiangshan-vdot/`。


## 1.1 昆明湖V2环境与hello验证
以下为原环境的部署和硬件构建操作记录：

```bash
cd ~/risc-v-compitition-26
git clone https://github.com/OpenXiangShan/xs-env.git
cd xs-env
sudo -s ./setup-tools.sh
source setup.sh
source env.sh
cd XiangShan
make init
make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j30
```

`setup-tools.sh`安装编译工具、依赖库、JDK、Mill和Verilator等；`setup.sh`初始化NEMU、nexus-am、DRAMsim3、XiangShan及其构建依赖。`env.sh`设置`NOOP_HOME`、`AM_HOME`等路径，每次新开终端后需重新加载。`make init`准备香山子模块，`make emu`生成RTL、转换为C++并编译主机仿真器。

在上述终端执行（需要先进行emu的编译）：

```bash
bash stage1/run-hello.sh
```

脚本核验构建配置，重新编译[hello.c](hello/hello.c)，运行后检查指定输出、GOOD TRAP及退出码：

```text
hello xiangshan, I am lzw-super, IP SZU.
```

每次运行在 `stage1/logs/` 新建目录，保存环境、构建配置、源码、镜像和仿真日志。[latest.txt](logs/latest.txt)记录最近成功运行目录的绝对路径。


## 1.2 向量加法生命周期

配置为VLEN=128、SEW=8、LMUL=1、VL=4，无掩码、ta/ma。输入[1,2,3,4]与[10,20,30,40]，检查结果[11,22,33,44]。报告记录取指、译码、重命名、分发、发射、执行、写回和提交八个阶段。

```bash
# 从PROJECT根目录构建程序、运行并生成VCD
WAVE=1 BEGIN=0 END=5000 bash stage1/vector-add/run.sh 00_vl4_ta
```

源码为[00_vl4_ta.S](vector-add/00_vl4_ta.S)，每次运行记录保存在 `stage1/vector-add/runs/`；[latest-00_vl4_ta.txt](vector-add/runs/latest-00_vl4_ta.txt)记录最近成功运行目录的绝对路径。

