#!/usr/bin/env python3
"""Apply design patches to pinned clean repositories; never checks out/resets an existing tree."""

from common import *
import argparse

p = argparse.ArgumentParser()
p.add_argument("--apply", action="store_true")
a = p.parse_args()
xs = envroot()
jobs = [
    (
        xs / "XiangShan",
        RTL / "base-commit.txt",
        [RTL / "xiangshan-vdot.patch", ROOT / "patches/build-compat.patch"],
        RTL / "source.sha256",
    ),
    (
        xs / "NEMU",
        NEMU / "base-commit.txt",
        [NEMU / "vdot-nemu.patch"],
        NEMU / "source.sha256",
    ),
]
# Validate both targets before mutating either one.
plans = []
for repo, base, patches, manifest in jobs:
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    assert (
        head == base.read_text().strip()
    ), f"{repo}: wrong base; use the documented NEW dedicated checkout, not an existing modified worktree"
    checks = [
        subprocess.run(
            ["git", "apply", "--reverse", "--check", str(patch)],
            cwd=repo,
            capture_output=True,
        ).returncode
        == 0
        for patch in patches
    ]
    if all(checks):
        check_sources(repo, manifest)
        print("ALREADY PREPARED:", repo)
        continue
    assert not any(checks), f"Partially patched tree: {repo}; inspect it manually"
    # Ignore nested submodule states, but refuse local/untracked files in the parent.
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--ignore-submodules=all"], cwd=repo, text=True
    )
    assert not status, f"{repo}: worktree not clean; no reset or overwrite performed"
    for patch in patches:
        run(["git", "apply", "--check", patch], cwd=repo)
    plans.append((repo, patches, manifest))
for repo, patches, manifest in plans:
    if a.apply:
        for patch in patches:
            run(["git", "apply", patch], cwd=repo)
        check_sources(repo, manifest)
        print("APPLIED:", repo)
    else:
        print("CHECK PASS, use --apply to patch:", repo)
