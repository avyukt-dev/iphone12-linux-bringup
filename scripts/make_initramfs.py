#!/usr/bin/env python3
"""Build deterministic ARM64 initramfs (cpio newc + gzip), optionally with BusyBox.

The optional BusyBox binary is built from its separate GPL-2.0 source by
scripts/build_busybox.sh. Packaging is host-side only; no device is accessed.
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


def build_cpio(init_elf: bytes, busybox_elf: bytes | None = None) -> bytes:
    require_arm64_elf(init_elf)
    if busybox_elf is not None:
        require_arm64_elf(busybox_elf)
    out = bytearray()
    names = ('dev', 'proc', 'sys', 'bin') + (('www',) if busybox_elf is not None else ())
    ino = 1
    for name in names:
        _append_entry(out, name, stat.S_IFDIR | 0o755, b'', ino)
        ino += 1
    # Kernel creates device from cpio metadata: host needs no root/mknod.
    _append_entry(out, 'dev/console', stat.S_IFCHR | 0o600, b'', ino,
                  rdevmajor=5, rdevminor=1)
    ino += 1
    _append_entry(out, 'init', stat.S_IFREG | 0o755, init_elf, ino)
    ino += 1
    if busybox_elf is not None:
        _append_entry(out, 'bin/busybox', stat.S_IFREG | 0o755, busybox_elf, ino)
        ino += 1
        # Explicit applets rather than an unpredictable, ambient host PATH.
        for applet in ('sh', 'ls', 'cat', 'mount', 'ip', 'httpd', 'uname', 'ps', 'echo'):
            _append_entry(out, f'bin/{applet}', stat.S_IFLNK | 0o777,
                          b'busybox', ino)
            ino += 1
        _append_entry(out, 'www/index.html', stat.S_IFREG | 0o644,
                      b'A14 Linux host-built userspace test page\n', ino)
        ino += 1
    _append_entry(out, 'TRAILER!!!', 0, b'', ino)
    return bytes(out)


def build_gzip(init_elf: bytes, busybox_elf: bytes | None = None) -> bytes:
    return gzip.compress(build_cpio(init_elf, busybox_elf), compresslevel=9, mtime=0)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--init', dest='executable', required=True, type=Path)
    p.add_argument('--busybox', type=Path, help='Separately built static GPL BusyBox for shell and HTTP applets')
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    data = build_gzip(args.executable.read_bytes(),
                      args.busybox.read_bytes() if args.busybox else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f'host-only initramfs: {args.output} ({len(data)} bytes compressed)')


if __name__ == '__main__':
    main()
