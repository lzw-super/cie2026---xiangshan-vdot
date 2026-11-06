#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
case_name=${1:-00_vl4_ta}
case "$case_name" in 00_vl4_ta) ;; *) echo 'Unknown case' >&2; exit 2;; esac
xs_root=${XS_ENV_ROOT:-$(realpath "$here/../../../xs-env")}
emu=${EMU:-$xs_root/XiangShan/build/emu}
run_dir="$here/runs/$(TZ=Asia/Shanghai date +%Y%m%d-%H%M%S)-$$-$case_name"
mkdir -p "$run_dir"
{
  date -Iseconds
  "$emu" --help 2>&1 | head -5 || true
  "${CROSS:-riscv64-linux-gnu-}gcc" --version | head -1
  git -C "$xs_root/XiangShan" rev-parse HEAD
  git -C "$xs_root/XiangShan" status --short
  sha256sum "$emu"
} > "$run_dir/environment.log"
make -C "$here" all 2>&1 | tee "$run_dir/build.log"
cp "$here/$case_name.S" "$here"/{link.ld,Makefile,run.sh} "$run_dir/"
cp "$here/build/$case_name".{bin,elf,dis,symbols} "$run_dir/"
sha256sum "$run_dir/$case_name".{bin,elf} > "$run_dir/artifacts.sha256"
args=(-i "$run_dir/$case_name.bin" -C "${MAX_CYCLES:-20000}" --ram-size 128MB)
if [[ -n ${DIFF_REF:-} ]]; then args+=(--diff "$DIFF_REF"); else args+=(--no-diff); fi
if [[ ${WAVE:-1} == 1 ]]; then
  args+=(--dump-wave --dump-wave-full --wave-path "$run_dir/wave.vcd" -b "${BEGIN:-0}" -e "${END:-5000}")
fi
printf '%q ' "$emu" "${args[@]}" > "$run_dir/command.txt"
printf '\n' >> "$run_dir/command.txt"
set +e
(cd "$run_dir" && "$emu" "${args[@]}") > "$run_dir/emu.log" 2>&1
rc=$?
set -e
sed -E 's/\x1B\[[0-9;]*[mK]//g' "$run_dir/emu.log" | rg 'TRAP|instrCnt|cycleCnt|Guest cycle|Host time' > "$run_dir/summary.txt" || true
cat "$run_dir/summary.txt"
printf 'emu_exit_code=%s\n' "$rc" > "$run_dir/result.txt"
if [[ $rc == 0 ]] && rg -q 'HIT GOOD TRAP' "$run_dir/emu.log"; then
  echo 'self_check=PASS' >> "$run_dir/result.txt"
  printf '%s\n' "$run_dir" > "$here/runs/latest-$case_name.txt"
  echo "PASS: $run_dir"
else
  echo 'self_check=FAIL' >> "$run_dir/result.txt"
  echo "FAIL: inspect $run_dir/emu.log" >&2
  exit 1
fi
