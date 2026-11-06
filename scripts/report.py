#!/usr/bin/env python3
from common import *
import argparse
import gzip
import re

p = argparse.ArgumentParser()
p.add_argument("run_dir", nargs="?", type=Path)
a = p.parse_args()
folder = a.run_dir or Path(
    json.loads((ROOT / "results/latest.json").read_text())["run"]
)
d = json.loads((folder / "results.json").read_text())
assert d["identity"]["mode"] == "difftest"
cases = {x["name"]: x for x in d["results"]}
for name, c in cases.items():
    data = gzip.decompress((folder / name / "emu.log.gz").read_bytes())
    assert c["pass_check"] and c["exit_code"] == 0
    assert (
        hashlib.sha256(data).hexdigest() == c["log_sha256"]
        and sha(folder / name / (name + ".bin")) == c["image_sha256"]
    )
    assert (
        b"Difftest enabled." in data
        and b"HIT GOOD TRAP" in data
        and b"ABORT at pc" not in data
    )
    stat = re.search(rb"instrCnt = ([\d,]+), cycleCnt = ([\d,]+)", data)
    assert stat and int(stat[2].replace(b",", b"")) == c["cycles"]
lines = [
    "# 当前设计复现性能结果",
    "",
    "完整程序cycleCnt，包含启动、配置、循环、自检。本表仅汇总本次运行。",
    "",
    f"DUT SHA256: `{d['identity']['emu_sha256']}`",
    f"REF SHA256: `{d['identity']['reference_sha256']}`",
    "",
    "| 次数 | RVV周期 | vdot周期 | RVV/vdot | 周期减少 |",
    "|---:|---:|---:|---:|---:|",
]
for n in [1, 32, 128]:
    r, v = cases.get(f"bench_rvv_{n}"), cases.get(f"bench_vdot_{n}")
    if r and v:
        lines.append(
            f"| {n} | {r['cycles']} | {v['cycles']} | {r['cycles']/v['cycles']:.4f}× | {(1-v['cycles']/r['cycles'])*100:.2f}% |"
        )
    else:
        lines.append(f"| {n} | 未运行完整配对 | — | — | — |")
(folder / "性能报告.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
