#!/usr/bin/env bash
# Prepare stage2 on the original pinned XiangShan sources. Does not build emu.
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
xs_root=${XS_ENV_ROOT:-$(realpath "$project_dir/../xs-env")}
rtl_dir="$xs_root/XiangShan"
base_commit=$(cat "$project_dir/stage2/2.2_rtl/base-commit.txt")
function_patch="$project_dir/stage2/2.2_rtl/xiangshan-vdot.patch"
compat_patch="$project_dir/patches/build-compat.patch"
template_commit=b60145df61e9202053e0b6d09c54c774fcc47639

if [[ $(git -C "$rtl_dir" rev-parse HEAD) != "$base_commit" ]]; then
    echo "XiangShan must be at $base_commit; see stage2/README.md. No checkout/reset performed." >&2
    exit 2
fi
if git -C "$rtl_dir" apply --reverse --check "$function_patch" 2>/dev/null; then
    (cd "$rtl_dir" && sha256sum -c "$project_dir/stage2/2.2_rtl/source.sha256")
    echo 'Stage2 functional sources already prepared.'
else
    if [[ -n $(git -C "$rtl_dir" status --porcelain --ignore-submodules=all) ]]; then
        echo 'XiangShan has local or untracked changes; inspect them before preparing stage2.' >&2
        exit 2
    fi
    git -C "$rtl_dir" apply --check "$function_patch"
    git -C "$rtl_dir" apply --check "$compat_patch"
    git -C "$rtl_dir" apply "$function_patch"
fi
if ! git -C "$rtl_dir" apply --reverse --check "$compat_patch" 2>/dev/null; then
    git -C "$rtl_dir" apply --check "$compat_patch"
    git -C "$rtl_dir" apply "$compat_patch"
fi
(cd "$rtl_dir" && sha256sum -c "$project_dir/stage2/2.2_rtl/source.sha256")

# This baseline does not register a chisel-template gitlink; make init cannot clone it.
if [[ ! -e "$rtl_dir/chisel-template" ]]; then
    git clone https://github.com/chipsalliance/chisel-template.git "$rtl_dir/chisel-template"
    git -C "$rtl_dir/chisel-template" checkout --detach "$template_commit"
fi
if [[ $(git -C "$rtl_dir/chisel-template" rev-parse HEAD) != "$template_commit" ]]; then
    echo "chisel-template must be at $template_commit; existing checkout was not changed." >&2
    exit 2
fi
if [[ -n $(git -C "$rtl_dir/chisel-template" status --porcelain) ]]; then
    echo 'chisel-template has local changes; inspect them before building.' >&2
    exit 2
fi
make -C "$rtl_dir" init
make -C "$project_dir/stage2/2.3_tests" verify
printf '\nStage2 sources and test images prepared. Compile emu manually:\n'
printf '  cd %q\n' "$rtl_dir"
printf '  source %q\n' "$xs_root/env.sh"
printf '  make emu CONFIG=KunminghuV2Config EMU_TRACE=1 -j30\n'
printf '\nThen run the commands in stage2/README.md.\n'
