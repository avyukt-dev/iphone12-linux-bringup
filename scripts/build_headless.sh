#!/usr/bin/env bash
# Compile and validate a host-only AArch64 Linux early-init image.
# Does not connect to, flash, reboot, or otherwise communicate with an iPhone.
set -euo pipefail
cd "$(dirname "$0")/.."

for tool in aarch64-linux-gnu-gcc aarch64-linux-gnu-readelf qemu-aarch64 python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing host tool: $tool" >&2
    echo 'On Ubuntu: sudo apt install gcc-aarch64-linux-gnu libc6-dev-arm64-cross binutils-aarch64-linux-gnu qemu-user python3' >&2
    exit 1
  fi
done

mkdir -p build/headless
aarch64-linux-gnu-gcc -std=c11 -O2 -Wall -Wextra -Werror -static -no-pie \
  -Wl,-z,max-page-size=0x4000 -Wl,-z,common-page-size=0x4000 \
  -o build/headless/init userspace/early_init.c

# Distinguish an ELF header from a usable executable with 16KiB segments.
python3 scripts/verify_arm64_elf.py build/headless/init
qemu-aarch64 build/headless/init --self-test |
  grep -Fx 'A14_HOST_EARLY_INIT_SELF_TEST_OK'
if [[ "${1:-}" == "--with-busybox" ]]; then
  [[ -f build/headless/busybox ]] || { echo "Build BusyBox first: bash scripts/build_busybox.sh" >&2; exit 1; }
  python3 scripts/verify_arm64_elf.py build/headless/busybox
  python3 scripts/make_initramfs.py --init build/headless/init \
    --busybox build/headless/busybox \
    --output build/headless/early-initramfs.cpio.gz
else
  python3 scripts/make_initramfs.py --init build/headless/init \
    --output build/headless/early-initramfs.cpio.gz
fi
echo 'HOST_ONLY_ARM64_EARLY_INIT_BUILD_OK'
