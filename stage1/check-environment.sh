#!/usr/bin/env bash
# Read-only audit of the installed xs-env toolchain and existing emu build.
set -euo pipefail
stage_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
xs_env_root=${XS_ENV_ROOT:-$(realpath "$stage_dir/../../xs-env")}
source "$xs_env_root/env.sh"
emu=${EMU:-$NOOP_HOME/build/emu}
printf 'audit_time='; TZ=Asia/Shanghai date --iso-8601=seconds
cat /etc/os-release
uname -srmo
printf 'cpu_threads='; getconf _NPROCESSORS_ONLN
printf '\nTool paths and versions\n'
for tool in git make g++ cmake python3 java mill verilator riscv64-linux-gnu-gcc; do
  command -v "$tool"
done
git --version
make --version | sed -n '1p'
g++ --version | sed -n '1p'
cmake --version | sed -n '1p'
python3 --version
java -version 2>&1
printf 'JAVA_HOME=%s\n' "${JAVA_HOME:-<unset>}"
# Mill must run inside the project so .mill-version selects the required release.
(cd "$NOOP_HOME" && mill --version)
verilator --version
riscv64-linux-gnu-gcc --version | sed -n '1p'
printf '\nInstalled dependency packages\n'
dpkg-query -W -f='${binary:Package}=${Version}\n' git make g++ cmake zlib1g-dev libsqlite3-dev libzstd-dev libreadline-dev libsdl2-dev device-tree-compiler g++-riscv64-linux-gnu 2>&1 || true
printf '\nRepositories\n'
for repo in "$xs_env_root" "$NOOP_HOME" "$NEMU_HOME" "$AM_HOME" "$NOOP_HOME/difftest" "$NOOP_HOME/yunsuan"; do
  printf '\nrepository=%s\n' "$repo"
  git -C "$repo" rev-parse HEAD
  git -C "$repo" status --short
done
printf '\nExisting emu\n'
stat -c 'path=%n bytes=%s modified=%y' "$emu"
sha256sum "$emu"
printf '\nBuild provenance\n'
rg -F -- '--config KunminghuV2Config' "$NOOP_HOME/build/time.log"
rg 'Exit status:|Elapsed|^\[|^Sat' "$NOOP_HOME/build/time.log"
rg '^VM_TRACE( |_VCD |_FST )' "$NOOP_HOME/build/emu-compile/VSimTop_classes.mk"
