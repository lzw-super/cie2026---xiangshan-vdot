from pathlib import Path
import os
import json
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "stage2/2.2_rtl"
NEMU = ROOT / "stage3/3.1.1_NEMU"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def envroot():
    assert os.environ.get(
        "XS_ENV_ROOT"
    ), "Set XS_ENV_ROOT to the absolute path of your dedicated xs-env checkout"
    return Path(os.environ["XS_ENV_ROOT"]).resolve()


def hashes(path):
    return {
        n: d
        for d, n in (
            line.split("  ", 1) for line in Path(path).read_text().splitlines()
        )
    }


def check_sources(repo, manifest):
    for n, d in hashes(manifest).items():
        assert (repo / n).is_file() and sha(repo / n) == d, f"Source mismatch: {repo/n}"


def run(cmd, **kw):
    return subprocess.run([str(x) for x in cmd], check=True, **kw)


def emu_identity(path):
    digest = sha(path)
    record = ROOT / "results/captured-emu.json"
    assert record.exists(), "First run scripts/capture-emu.py after building emu"
    d = json.loads(record.read_text())
    assert d["emu_sha256"] == digest, "emu differs from captured design build"
    return d
