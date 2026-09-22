#!/usr/bin/env bash
# Host-only cross build of a *separate* GPL-2.0 BusyBox binary.
# Never connects to, reboots, flashes, or writes to an iPhone.
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=1.37.0
SHA256=3311dff32e746499f4df0d5df04d7eb396382d7e108bb9250e7b519b837043a4
ROOT="$PWD/build/busybox-src"
ARCHIVE="$PWD/build/busybox-$VERSION.tar.bz2"
URL="https://busybox.net/downloads/busybox-$VERSION.tar.bz2"

for tool in curl tar sha256sum make python3 aarch64-linux-gnu-gcc qemu-aarch64; do
  command -v "$tool" >/dev/null || { echo "Missing required host tool: $tool" >&2; exit 1; }
done

mkdir -p build/headless
if [[ ! -f "$ARCHIVE" ]]; then
  curl --fail --location --retry 2 --output "$ARCHIVE.tmp" "$URL"
  mv "$ARCHIVE.tmp" "$ARCHIVE"
fi
printf '%s  %s\n' "$SHA256" "$ARCHIVE" | sha256sum --check --status || {
  echo 'BusyBox source SHA-256 mismatch; refusing to execute source' >&2
  exit 1
}

if [[ ! -d "$ROOT" ]]; then
  mkdir -p "$ROOT"
  tar -xjf "$ARCHIVE" -C "$ROOT" --strip-components=1
fi

if [[ ! -f "$ROOT/.config" ]]; then
  make -C "$ROOT" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig
fi
# Modify only the checked-out source config, never vendor the GPL source/binary
# into the MIT-licensed workspace. Keep HTTP and shell applets enabled.
python3 - "$ROOT/.config" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
for symbol in ('STATIC', 'ASH', 'HTTPD', 'IP'):
    on, off = f'CONFIG_{symbol}=y', f'# CONFIG_{symbol} is not set'
    if off in s:
        s = s.replace(off, on)
    elif on not in s:
        raise SystemExit(f'Missing BusyBox CONFIG_{symbol}; audit upstream config before continuing')
# BusyBox 1.37.0 defaults to x86 SHA-NI acceleration and references x86-only
# sha1_process_block64_shaNI when cross-compiling for ARM64. Turn off both
# x86-specific options; do not patch the upstream GPL source.
for symbol in ('SHA1_HWACCEL', 'SHA256_HWACCEL'):
    s = s.replace(f'CONFIG_{symbol}=y', f'# CONFIG_{symbol} is not set')
p.write_text(s)
PY
make -C "$ROOT" -j2 ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
  LDFLAGS='--static' busybox
install -m 0755 "$ROOT/busybox" build/headless/busybox
python3 scripts/verify_arm64_elf.py build/headless/busybox
qemu-aarch64 build/headless/busybox sh -c 'echo A14_HOST_BUSYBOX_SHELL_OK' |
  grep -Fx 'A14_HOST_BUSYBOX_SHELL_OK'
qemu-aarch64 build/headless/busybox --list |
  grep -Fx httpd
echo 'HOST_ONLY_ARM64_BUSYBOX_BUILD_OK'
