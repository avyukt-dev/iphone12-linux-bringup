#!/usr/bin/env python3
"""Build a deterministic, minimal ARM64 initramfs (cpio newc + gzip).

Host-side packaging only: image has /init and /dev/console, NOT a shell,
networking, Apple drivers, bootloader, kernel, or firmware.
"""
import argparse
import gzip
from pathlib import Path
import stat
import struct

ARM64_MACHINE = 183


def require_arm64_elf(blob: bytes) -> None:
    if len(blob) < 64 or blob[:4] != b'\x7fELF':
        raise ValueError('input is not an ELF executable')
    if blob[4] != 2 or blob[5] != 1:
        raise ValueError('input must be ELF64 little-endian')
    if struct.unpack_from('<H', blob, 18)[0] != ARM64_MACHINE:
        raise ValueError('input must target AArch64 (ELF e_machine=183)')
    if struct.unpack_from('<H', blob, 16)[0] not in (2, 3):
        raise ValueError('input must be a linked ELF executable (ET_EXEC/ET_DYN)')


def _pad4(out: bytearray) -> None:
    out.extend(b'\x00' * (-len(out) % 4))


def _append_entry(
    out: bytearray, name: str, mode: int, payload: bytes,
    ino: int, rdevmajor: int = 0, rdevminor: int = 0,
) -> None:
    encoded = name.encode('ascii') + b'\x00'
    # cpio 'newc' header: 070701 followed by thirteen eight-digit hex fields.
    fields = (ino, mode, 0, 0, 2 if stat.S_ISDIR(mode) else 1,
              0, len(payload), 0, 0, rdevmajor, rdevminor, len(encoded), 0)
    out.extend(b'070701' + b''.join(f'{field:08x}'.encode('ascii') for field in fields))
    out.extend(encoded)
    _pad4(out)
    out.extend(payload)
    _pad4(out)


def build_cpio(init_elf: bytes) -> bytes:
    require_arm64_elf(init_elf)
    out = bytearray()
    dirs = ('dev', 'proc', 'sys', 'bin')
    for ino, name in enumerate(dirs, start=1):
        _append_entry(out, name, stat.S_IFDIR | 0o755, b'', ino)
    # Kernel creates this character device from cpio metadata; no mknod
    # permission or root privileges are needed to construct the archive.
    _append_entry(out, 'dev/console', stat.S_IFCHR | 0o600, b'', 5,
                  rdevmajor=5, rdevminor=1)
    _append_entry(out, 'init', stat.S_IFREG | 0o755, init_elf, 6)
    _append_entry(out, 'TRAILER!!!', 0, b'', 7)
    return bytes(out)


def build_gzip(init_elf: bytes) -> bytes:
    return gzip.compress(build_cpio(init_elf), compresslevel=9, mtime=0)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--init', dest='executable', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    data = build_gzip(args.executable.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f'host-only initramfs: {args.output} ({len(data)} bytes compressed)')


if __name__ == '__main__':
    main()
