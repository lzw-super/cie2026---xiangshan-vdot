#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
: "${XS_ENV_ROOT:?Set XS_ENV_ROOT to the dedicated xs-env checkout}"
export NEMU_HOME=$(realpath "$XS_ENV_ROOT/NEMU")
python3 - "$project_dir" "$NEMU_HOME" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/'scripts'))
from common import check_sources,NEMU
check_sources(Path(sys.argv[2]),NEMU/'source.sha256')
PY
mkdir -p "$project_dir/build/nemu" "$project_dir/results"
make -C "$NEMU_HOME" riscv64-xs-kmhv2-vdot-ref_defconfig
make -C "$NEMU_HOME" BUILD_DIR="$project_dir/build/nemu" -j"${JOBS:-12}"
cmp "$NEMU_HOME/.config" "$project_dir/stage3/3.1.1_NEMU/ref.config"
gcc -D__ISA__=riscv64 -I"$NEMU_HOME/include" -I"$NEMU_HOME/src/isa/riscv64/include" -I"$NEMU_HOME/lib-include" \
 "$project_dir/stage3/3.1.1_NEMU/tests/nemu_model_test.c" -ldl -o "$project_dir/build/nemu-model-test"
"$project_dir/build/nemu-model-test" "$project_dir/build/nemu/riscv64-nemu-interpreter-so" | tee "$project_dir/results/nemu-model-test.log"
python3 - "$project_dir" <<'PY'
import sys,json,hashlib
from pathlib import Path
p=Path(sys.argv[1]);ref=p/'build/nemu/riscv64-nemu-interpreter-so'
assert 'PASS: actual NEMU model' in (p/'results/nemu-model-test.log').read_text()
(p/'results/nemu-build.json').write_text(json.dumps(dict(reference_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),model_test='PASS'),indent=2)+'\n')
PY
