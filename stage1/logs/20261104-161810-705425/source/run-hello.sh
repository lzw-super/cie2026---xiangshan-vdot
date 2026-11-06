#!/usr/bin/env bash
set -euo pipefail
stage_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
xs_env_root=${XS_ENV_ROOT:-$(realpath "$stage_dir/../../xs-env")}
run_dir="$stage_dir/logs/$(TZ=Asia/Shanghai date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$run_dir/config-evidence" "$run_dir/source"
source "$xs_env_root/env.sh" > "$run_dir/environment.log"
emu=${EMU:-$NOOP_HOME/build/emu}
# Verify the recorded RTL configuration and trace-enabled generated build.
rg -Fq -- '--config KunminghuV2Config' "$NOOP_HOME/build/time.log"
rg -q '^VM_TRACE = 1$' "$NOOP_HOME/build/emu-compile/VSimTop_classes.mk"
"$stage_dir/check-environment.sh" >> "$run_dir/environment.log" 2>&1
"$emu" --help > "$run_dir/emu-help.txt" 2>&1
cp "$NOOP_HOME/build/time.log" "$run_dir/config-evidence/emu-build-time.log"
cp "$NOOP_HOME/build/emu-compile/VSimTop_classes.mk" "$run_dir/config-evidence/"
cp "$NOOP_HOME/.mill-version" "$NOOP_HOME/src/main/scala/top/Configs.scala" "$run_dir/config-evidence/"
cp "$xs_env_root"/{setup-tools.sh,setup.sh,env.sh} "$run_dir/config-evidence/"
cp "$stage_dir/hello"/{hello.c,Makefile} "$stage_dir"/{run-hello.sh,check-environment.sh} "$run_dir/source/"
python3 - "$run_dir/deployment-history.log" <<'PY'
from pathlib import Path
import sys
history=Path.home()/'.bash_history'
exact={'git clone https://github.com/OpenXiangShan/xs-env.git','sudo -s ./setup-tools.sh','source setup.sh','source env.sh','make init','make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j30','make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j32'}
lines=['Relevant historical commands; individual execution times are not stored.','Current successful emu build is evidenced separately by config-evidence/emu-build-time.log.']
if history.exists():
    lines += [f'history_line_{i}: {s.strip()}' for i,s in enumerate(history.read_text(errors='replace').splitlines(),1) if s.strip() in exact]
Path(sys.argv[1]).write_text('\n'.join(lines)+'\n')
PY
{
  make -C "$stage_dir/hello" ARCH=riscv64-xs LINUX_GNU_TOOLCHAIN=1 clean
  make -C "$stage_dir/hello" ARCH=riscv64-xs LINUX_GNU_TOOLCHAIN=1
} > "$run_dir/build.log" 2>&1
image="$stage_dir/hello/build/stage1-hello-riscv64-xs.bin"
elf="$stage_dir/hello/build/stage1-hello-riscv64-xs.elf"
cp "$image" "$elf" "$stage_dir/hello/build/stage1-hello-riscv64-xs.txt" "$run_dir/"
sha256sum "$run_dir/stage1-hello-riscv64-xs".{bin,elf} > "$run_dir/artifacts.sha256"
sha256sum "$emu" "$stage_dir/hello/hello.c" >> "$run_dir/environment.log"
args=(-i "$run_dir/stage1-hello-riscv64-xs.bin" -C 100000 --ram-size 128MB --no-diff)
printf '%q ' "$emu" "${args[@]}" > "$run_dir/command.txt"
printf '\n' >> "$run_dir/command.txt"
set +e
(cd "$run_dir" && "$emu" "${args[@]}") > "$run_dir/emu.log" 2>&1
run_status=$?
set -e
python3 - "$run_dir/emu.log" "$run_dir/summary.txt" <<'PY'
from pathlib import Path
import re,sys
s=Path(sys.argv[1]).read_text(errors='replace').replace('\\u001b','\x1b')
s=re.sub(r'\x1b\[[0-9;]*[mK]','',s)
keys=['emu compiled at','hello xiangshan, I am lzw-super, IP SZU.','TRAP','instrCnt','Guest cycle spent','Host time spent']
Path(sys.argv[2]).write_text('\n'.join(line for line in s.splitlines() if any(k in line for k in keys))+'\n')
PY
cat "$run_dir/summary.txt"
printf 'emu_exit_code=%s\n' "$run_status" > "$run_dir/result.txt"
[[ "$run_status" == 0 ]]
rg -Fq 'hello xiangshan, I am lzw-super, IP SZU.' "$run_dir/emu.log"
rg -Fq 'HIT GOOD TRAP' "$run_dir/emu.log"
printf 'hello_output=PASS\ngood_trap=PASS\n' >> "$run_dir/result.txt"
printf '%s\n' "$run_dir" > "$stage_dir/logs/latest.txt"
printf '\n验证通过；原始日志：%s\n' "$run_dir"
