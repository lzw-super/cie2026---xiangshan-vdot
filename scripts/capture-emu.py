#!/usr/bin/env python3
"""Capture a freshly built four-stage design. Existing validation identities are preserved."""

from common import *
import re

xs = envroot() / "XiangShan"
check_sources(xs, RTL / "source.sha256")
base = (RTL / "base-commit.txt").read_text().strip()
assert (
    subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=xs, text=True).strip()
    == base
)
# Configs.scala is not modified by the extension; forbid replacing the default config.
assert (
    xs / "src/main/scala/top/Configs.scala"
).read_bytes() == subprocess.check_output(
    ["git", "show", base + ":src/main/scala/top/Configs.scala"], cwd=xs
)
log = (xs / "build/time.log").read_text()
configs = re.findall(r"--config (\w+)", log)
assert (
    configs and configs[-1] == "KunminghuV2Config"
), "Latest build must be KunminghuV2Config"
latest = log.rsplit("[mill]", 1)[-1]
v = latest.rfind("[verilator]")
c = latest.rfind("[c++]")
assert 0 <= v < c
for block in [latest[: latest.find("[verilator]")], latest[v:c], latest[c:]]:
    statuses = re.findall(r"Exit status:\s*(\d+)", block)
    assert statuses and statuses[-1] == "0", "Build incomplete/failed"
mdir = re.findall(r"-Mdir\s+(\S+)", latest)
assert mdir
compile = Path(mdir[-1])
compile = compile if compile.is_absolute() else xs / compile
trace = compile / "VSimTop_classes.mk"
assert re.search(r"^VM_TRACE\s*=\s*1\s*$", trace.read_text(), re.M)
emu = xs / "build/emu"
rtl = xs / "build/rtl/SimTop.sv"
for file in [rtl, trace] + [
    xs / n for n in hashes(RTL / "source.sha256") if n.startswith("src/main/")
]:
    assert emu.stat().st_mtime_ns >= file.stat().st_mtime_ns, f"emu older than {file}"
record = dict(
    config="KunminghuV2Config",
    kind="NEW_DESIGN_BUILD",
    emu_sha256=sha(emu),
    rtl_sha256=sha(rtl),
    build_log_sha256=sha(xs / "build/time.log"),
    source_sha256=hashes(RTL / "source.sha256"),
    base=base,
)
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results/captured-emu.json").write_text(json.dumps(record, indent=2) + "\n")
print("Captured design identity:", record["emu_sha256"])
