#!/usr/bin/env bash
# Source checkout only: never flashes or modifies a connected device.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v git >/dev/null || { echo 'git is required' >&2; exit 1; }

with_kernel=0
with_sandcastle=0
for arg in "$@"; do
  case "$arg" in
    --with-kernel) with_kernel=1 ;;
    --with-sandcastle-kernel) with_sandcastle=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 64 ;;
  esac
done
mkdir -p vendor
clone_one() {
  local name="$1" branch="$2" url="$3"
  if [[ -d "vendor/$name/.git" ]]; then
    echo "vendor/$name already cloned; preserving working tree"
  elif [[ -e "vendor/$name" ]]; then
    echo "vendor/$name exists but is not a Git clone; refusing to overwrite" >&2; exit 1
  else
    git clone --depth=1 --single-branch --branch "$branch" "$url" "vendor/$name"
  fi
}
clone_one docs master https://github.com/HoolockLinux/docs.git
clone_one m1n1 research/iphone12-a14 https://github.com/avyukt-dev/m1n1.git
# Hoolock m1n1 depends on Git submodules for a complete source checkout.
git -C vendor/m1n1 submodule update --init --recursive
clone_one HoolockRD master https://github.com/HoolockLinux/HoolockRD.git
clone_one projectsandcastle master https://github.com/corellium/projectsandcastle.git
if (( with_kernel )); then
  echo 'Kernel checkout may consume multiple GB of disk space.'
  clone_one linux research/iphone12-a14 https://github.com/avyukt-dev/linux.git
fi
if (( with_sandcastle )); then
  echo 'Sandcastle kernel checkout may consume substantial disk space.'
  clone_one linux-sandcastle sandcastle-5.4 https://github.com/corellium/linux-sandcastle.git
fi
: > vendor/UPSTREAM_COMMITS.txt
for path in vendor/*; do
  [[ -d "$path/.git" ]] || continue
  printf '%-22s %s %s\n' "${path#vendor/}" "$(git -C "$path" rev-parse HEAD)" "$(git -C "$path" remote get-url origin)" >> vendor/UPSTREAM_COMMITS.txt
done
printf '\nCheckout inventory: vendor/UPSTREAM_COMMITS.txt\n'
