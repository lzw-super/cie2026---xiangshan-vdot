#!/usr/bin/env python3
"""Offline source-package checks. Does not run RTL/NEMU or audit excluded logs."""

from common import *

check_sources(RTL, RTL / "source.sha256")
check_sources(NEMU / "source", NEMU / "source.sha256")
hardware = ROOT / "stage3/hardware"
check_sources(hardware, hardware / "source.sha256")
versions = json.loads((ROOT / "versions.json").read_text())
assert (RTL / "base-commit.txt").read_text().strip() == versions["XiangShan"]
assert (NEMU / "base-commit.txt").read_text().strip() == versions["NEMU"]

checked = 0
for suite in ("00_smoke", "01_directed"):
    source = ROOT / "stage2/2.3_tests/suites" / suite / "source"
    for name in (suite + ".S", "common.S", "link.ld"):
        assert (source / name).is_file(), f"Missing test source: {source/name}"
    records = json.loads((source / (suite + ".json")).read_text())
    assert len(records) == (1 if suite == "00_smoke" else 10)
    for case in records:

        def signed8(value):
            value &= 255
            return value - 256 if value >= 128 else value

        total = sum(
            signed8(a) * signed8(b) for a, b in zip(case["a"][:8], case["b"][:8])
        )
        expected = list((total & 0xFFFFFFFF).to_bytes(4, "little")) + [0] * 12
        assert case["expected"] == expected, f"Reference mismatch: {suite}/{case['id']}"
        word = 0xFE000057 | case["vs2"] << 20 | case["vs1"] << 15 | case["vd"] << 7
        assert int(case["instruction"], 16) == word
        checked += 1

print(
    f"PASS: RTL/NEMU source manifests and {checked} test reference cases; no emulator run or log audit"
)
