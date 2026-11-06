#!/usr/bin/env python3
"""Portable design runner. No full emu build is performed."""

from common import *
import argparse
import datetime
import gzip
import re
import shutil

p = argparse.ArgumentParser()
g = p.add_mutually_exclusive_group()
g.add_argument("--all", action="store_true")
g.add_argument("--baseline", action="store_true")
g.add_argument("--stage2", action="store_true")
p.add_argument("--case", default="00_smoke")
p.add_argument("--emu", type=Path)
p.add_argument("--ref", type=Path)
p.add_argument("--wave", action="store_true")
a = p.parse_args()
emu = (a.emu or envroot() / "XiangShan/build/emu").resolve()
identity = emu_identity(emu)
ref = (a.ref or ROOT / "build/nemu/riscv64-nemu-interpreter-so").resolve()
boot = NEMU / "boot.bin"
functional = ROOT / "stage3/3.1.2_协同仿真/programs"
bench = ROOT / "stage3/3.2_RVV基线"
run(["make", "-C", functional, "all"])
run(["make", "-C", bench, "all"])
images = {
    f.stem: f
    for folder in [functional, bench]
    for f in (folder / "build").glob("*.bin")
}
names = (
    sorted(images)
    if a.all
    else (
        ["00_smoke", "01_directed"]
        if a.stage2
        else (
            sorted(f.stem for f in (bench / "build").glob("*.bin"))
            if a.baseline
            else [a.case]
        )
    )
)
assert all(n in images for n in names)
if not a.stage2:
    assert ref.is_file(), "Build NEMU first or specify --ref"
    digest = sha(ref)
    record = ROOT / "results/nemu-build.json"
    assert (
        record.is_file()
    ), "Build and validate the reference with scripts/build-nemu.sh"
    reference_record = json.loads(record.read_text())
    assert (
        reference_record["reference_sha256"] == digest
    ), "Reference differs from validated NEMU build"
    assert reference_record["model_test"] == "PASS", "NEMU model test must pass first"
stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime(
    "%Y%m%d-%H%M%S-%f"
)
folder = ROOT / "results/runs" / stamp
folder.mkdir(parents=True)
identity.update(
    boot_sha256=sha(boot),
    mode="no-diff" if a.stage2 else "difftest",
    reference_sha256=None if a.stage2 else sha(ref),
)
results = []
for name in names:
    case = folder / name
    case.mkdir()
    image = images[name]
    for ext in [".bin", ".elf", ".S", ".dis", ".symbols"]:
        src = image.with_suffix(ext)
        if src.exists():
            shutil.copy2(src, case / src.name)
    cmd = [
        str(emu),
        "-i",
        str(case / image.name),
        "-C",
        "200000",
        "--ram-size",
        "128MB",
        "--flash",
        str(boot),
    ]
    cmd += ["--no-diff"] if a.stage2 else ["--diff", str(ref)]
    if a.wave and name == "00_smoke":
        cmd += [
            "--dump-wave",
            "--dump-wave-full",
            "--wave-path",
            str(case / "wave.vcd"),
            "-b",
            "0",
            "-e",
            "12000",
        ]
    (case / "command.json").write_text(json.dumps(cmd, indent=2) + "\n")
    with (case / "emu.log").open("w") as f:
        proc = subprocess.run(cmd, cwd=case, stdout=f, stderr=subprocess.STDOUT)
    data = (case / "emu.log").read_bytes()
    stat = re.search(rb"instrCnt = ([\d,]+), cycleCnt = ([\d,]+)", data)
    passed = (
        proc.returncode == 0
        and b"HIT GOOD TRAP" in data
        and b"HIT BAD TRAP" not in data
        and b"ABORT at pc" not in data
        and bool(stat)
        and (a.stage2 or b"Difftest enabled." in data)
    )
    result = dict(
        name=name,
        pass_check=passed,
        exit_code=proc.returncode,
        image_sha256=sha(case / image.name),
        log_sha256=sha(case / "emu.log"),
    )
    if stat:
        result.update(
            instructions=int(stat[1].replace(b",", b"")),
            cycles=int(stat[2].replace(b",", b"")),
        )
    (case / "emu.log.gz").write_bytes(gzip.compress(data, mtime=0))
    (case / "emu.log").unlink()
    (case / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    results.append(result)
    (folder / "results.json").write_text(
        json.dumps(dict(identity=identity, results=results), indent=2) + "\n"
    )
    print(name, result, flush=True)
    assert passed, f"FAIL: {case}/emu.log.gz"
(ROOT / "results/latest.json").write_text(
    json.dumps(dict(run=str(folder)), indent=2) + "\n"
)
print("PASS:", folder)
