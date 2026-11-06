#!/usr/bin/env python3
"""Stream an emu VCD. Sample pre-rising-edge state; check actual FU math/tags/latency.
Uses this checkout's 256-entry ROB pointer ordering; fails if its width changes.
Does not infer commit/PRF correctness from FU valid alone.
"""

import argparse
import csv
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("vcd", type=Path)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
f = a.vcd.open()
scopes = []
defs = []
for line in f:
    t = line.split()
    if not t:
        continue
    if t[0] == "$scope":
        scopes.append(t[2])
    elif t[0] == "$upscope":
        scopes.pop()
    elif t[0] == "$var":
        defs.append((".".join(scopes), t[4], t[3], int(t[2])))
    elif t[0] == "$enddefinitions":
        break
fu = next(
    s.rsplit(".", 1)[0] for s, n, c, w in defs if n == "sum8" and s.endswith(".dot")
)
parent = fu.rsplit(".", 1)[0]
lookup = {(s, n): (c, w) for s, n, c, w in defs}
wanted = {}


def take(key, scope, name):
    wanted[key] = lookup[(scope, name)]


take("core_clock", "TOP", "clock")
for name in [
    "clock",
    "reset",
    "io_in_valid",
    "io_in_ready",
    "io_out_valid",
    "io_out_ready",
    "io_flush_valid",
    "io_flush_bits_robIdx_flag",
    "io_flush_bits_robIdx_value",
    "io_flush_bits_level",
    "io_out_bits_ctrl_robIdx_flag",
    "io_out_bits_ctrl_robIdx_value",
    "io_out_bits_ctrl_pdest",
    "io_out_bits_ctrl_exceptionVec_2",
    "io_out_bits_res_data",
]:
    take(name, fu, name)
for name in ["io_in_bits_robIdx_flag", "io_in_bits_robIdx_value", "io_in_bits_pdest"]:
    take(name, parent, name)
for name in (
    ["io_vs1", "io_vs2", "sum8"]
    + [f"io_enable_{i}" for i in range(4)]
    + [f"products_{i}" for i in range(8)]
    + [f"sums2_{i}" for i in range(4)]
    + [f"sums4_{i}" for i in range(2)]
):
    take(name, fu + ".dot", name)
assert wanted["io_in_bits_robIdx_value"][1] == 8
ids = {c for c, w in wanted.values()}
values = {}
before = {}
time = 0
cycle = 0
previous = None
pending = {}
events = []
kills = []
en_checks = 0
accepted = 0
flushes = 0
wave = (a.output / "selected.vcd").open("w")
wave.write("$timescale 1ps $end\n$scope module selected $end\n")
for name, (code, width) in wanted.items():
    wave.write(f"$var wire {width} {code} {name} $end\n")
wave.write("$upscope $end\n$enddefinitions $end\n")


def signed(x, n):
    return x - (1 << n) if x & (1 << (n - 1)) else x


def sample(v):
    return {
        k: int(v[c], 2) if set(v.get(c, "x")) <= set("01") else None
        for k, (c, w) in wanted.items()
    }


def check(s):
    global cycle, previous, en_checks, accepted, flushes
    cycle += 1
    if s["reset"]:
        previous = None
        pending.clear()
        return
    if previous:
        old = previous
        for stage, (prefix, count, width) in enumerate(
            [("products", 8, 16), ("sums2", 4, 17), ("sums4", 2, 18), ("sum8", 1, 19)]
        ):
            if old[f"io_enable_{stage}"]:
                for i in range(count):
                    if stage == 0:
                        expected = signed((old["io_vs1"] >> (8 * i)) & 255, 8) * signed(
                            (old["io_vs2"] >> (8 * i)) & 255, 8
                        )
                    else:
                        src = ["", "products", "sums2", "sums4"][stage]
                        expected = sum(
                            signed(old[f"{src}_{2*i+j}"], width - 1) for j in range(2)
                        )
                    name = prefix if stage == 3 else f"{prefix}_{i}"
                    assert s[name] == expected & ((1 << width) - 1), (
                        cycle,
                        name,
                        s[name],
                        expected,
                    )
                    en_checks += 1
    previous = s

    def tag(prefix):
        return s[prefix + "_robIdx_flag"] * 256 + s[prefix + "_robIdx_value"]

    if s["io_flush_valid"]:
        flushes += 1
        cut = tag("io_flush_bits")
        for key, item in list(pending.items()):
            diff = (key - cut) % 512
            if 0 < diff < 256 or (diff == 0 and s["io_flush_bits_level"]):
                kills.append(dict(cycle=cycle, tag=key, age=cycle - item["cycle"]))
                del pending[key]
    if s["io_out_valid"]:
        key = tag("io_out_bits_ctrl")
        assert key in pending, ("unexpected output", cycle, key)
        item = pending.pop(key)
        assert cycle - item["cycle"] == 4, ("latency", cycle, item)
        assert s["io_out_bits_ctrl_pdest"] == item["pdest"], ("pdest", cycle, item)
        assert s["io_out_bits_res_data"] == item["result"], (
            "result",
            cycle,
            item,
            s["io_out_bits_res_data"],
        )
        assert s["io_out_bits_ctrl_exceptionVec_2"] == 0, ("illegal", cycle)
        assert s["io_out_ready"] == 1, ("output not accepted", cycle)
        events.append(
            dict(
                input_cycle=item["cycle"],
                output_cycle=cycle,
                tag=key,
                pdest=item["pdest"],
                result=f'{item["result"]:032x}',
                input_time=item["time"],
                output_time=time,
            )
        )
    if s["io_in_valid"] and s["io_in_ready"]:
        key = tag("io_in_bits")
        result = (
            sum(
                signed((s["io_vs1"] >> (8 * i)) & 255, 8)
                * signed((s["io_vs2"] >> (8 * i)) & 255, 8)
                for i in range(8)
            )
            & 0xFFFFFFFF
        )
        # ExeUnit discards a same-cycle redirected input before its first shared stage.
        cut = tag("io_flush_bits") if s["io_flush_valid"] else 0
        diff = (key - cut) % 512
        killed = s["io_flush_valid"] and (
            0 < diff < 256 or diff == 0 and s["io_flush_bits_level"]
        )
        accepted += 1
        if killed:
            kills.append(dict(cycle=cycle, tag=key, age=0))
        else:
            assert key not in pending, ("tag reused in flight", key)
            pending[key] = dict(
                cycle=cycle, time=time, pdest=s["io_in_bits_pdest"], result=result
            )
    for key, item in pending.items():
        assert cycle - item["cycle"] <= 4, ("missing output", cycle, key, item)


def finish_block():
    if (
        before.get(wanted["core_clock"][0]) == "0"
        and values.get(wanted["core_clock"][0]) == "1"
    ):
        check(sample(before))


for line in f:
    if line.startswith("#"):
        finish_block()
        before = values.copy()
        time = int(line[1:])
        wave.write(line)
    elif line and line[0] in "01xz":
        code = line[1:].strip()
        if code in ids:
            values[code] = line[0]
            wave.write(line)
    elif line.startswith("b"):
        bits, code = line[1:].split()
        if code in ids:
            values[code] = bits
            wave.write(line)
finish_block()
wave.close()
f.close()
assert not pending, ("trace ended with pending instructions", pending)
assert events, "no vdot outputs captured"
with (a.output / "transactions.csv").open("w") as out:
    w = csv.DictWriter(out, fieldnames=list(events[0]))
    w.writeheader()
    w.writerows(events)
runs = []
n = 0
last = None
for event in events:
    c = event["input_cycle"]
    n = n + 1 if last is not None and c == last + 1 else 1
    runs.append(n)
    last = c
result = dict(
    source=str(a.vcd.resolve()),
    fu_scope=fu,
    cycles_sampled=cycle,
    inputs=accepted,
    outputs=len(events),
    arithmetic_register_checks=en_checks,
    latency_cycles=4,
    latency_vcd_ticks=sorted({e["output_time"] - e["input_time"] for e in events}),
    longest_contiguous_inputs=max(runs),
    flush_cycles=flushes,
    killed_transactions=kills,
    unmatched_pending=len(pending),
    status="PASS",
)
(a.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
