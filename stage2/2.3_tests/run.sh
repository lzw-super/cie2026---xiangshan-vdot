#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
suite=${1:-00_smoke}
case "$suite" in 00_smoke|01_directed) ;; *) echo 'Suite must be 00_smoke or 01_directed' >&2; exit 2;; esac
: "${EMU:?Set EMU to the absolute path of a KunminghuV2Config emu with this vdot extension}"
emu=$(realpath "$EMU")
[[ -x "$emu" ]] || { echo "Not executable: $emu" >&2; exit 2; }
make -C "$here" verify
mkdir -p "$here/runs"
run_dir=$(mktemp -d "$here/runs/$(date +%Y%m%d-%H%M%S)-$suite-XXXXXX")
cp "$here/build/$suite".{bin,elf} "$run_dir/"
args=(-i "$run_dir/$suite.bin" -C "${MAX_CYCLES:-200000}" --ram-size 128MB --no-diff)
if [[ ${WAVE:-0} == 1 ]]; then
 args+=(--dump-wave --dump-wave-full --wave-path "$run_dir/wave.vcd" -b "${BEGIN:-0}" -e "${END:-20000}")
fi
{
 date -Iseconds
 sha256sum "$emu" "$run_dir/$suite.bin"
 printf '%q ' "$emu" "${args[@]}"
 printf '\n'
} > "$run_dir/environment.log"
set +e
(cd "$run_dir" && "$emu" "${args[@]}") > "$run_dir/emu.log" 2>&1
rc=$?
set -e
printf 'emu_exit_code=%s\nmode=no-diff\n' "$rc" > "$run_dir/result.txt"
if [[ "$rc" == 0 ]] && grep -q 'HIT GOOD TRAP' "$run_dir/emu.log" && ! grep -q 'HIT BAD TRAP' "$run_dir/emu.log"; then
 echo 'self_check=PASS' >> "$run_dir/result.txt"
 echo "PASS: $run_dir"
else
 echo 'self_check=FAIL' >> "$run_dir/result.txt"
 echo "FAIL: inspect $run_dir/emu.log" >&2
 exit 1
fi
