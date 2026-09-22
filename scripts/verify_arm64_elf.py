#!/usr/bin/env python3
"""Reject ELF binaries that cannot serve as the project's 16-KiB static /init.

This is a host-side ELF format check, not Apple A14 hardware compatibility
or proof of successful native Linux boot.
"""
import argparse
import struct
from pathlib import Path

ELF_MAGIC = b'\x7fELF'
PT_LOAD = 1
PT_DYNAMIC = 2
PT_INTERP = 3
ALIGNMENT = 16384
EM_AARCH64 = 183


def inspect_elf(data: bytes) -> dict:
    if len(data) < 64 or data[:4] != ELF_MAGIC:
        raise ValueError('Expected a full ELF header')
    if data[4] != 2 or data[5] != 1 or data[6] != 1:
        raise ValueError('ELF must be 64-bit, little-endian, version 1')
    e_type, e_machine = struct.unpack_from('<HH', data, 16)
    if e_type != 2 or e_machine != EM_AARCH64:
        raise ValueError('Expected AArch64 ET_EXEC, not a host executable or shared library')
    phoff = struct.unpack_from('<Q', data, 32)[0]
    phentsize, phnum = struct.unpack_from('<HH', data, 54)
    if phnum < 1 or phentsize < 56 or phoff > len(data) or phoff + phentsize * phnum > len(data):
        raise ValueError('Invalid program header table')
    load_count = 0
    for index in range(phnum):
        offset = phoff + phentsize * index
        p_type, p_flags, p_offset, p_vaddr, _, p_filesz, p_memsz, p_align = (
            struct.unpack_from('<IIQQQQQQ', data, offset)
        )
        if p_type in (PT_DYNAMIC, PT_INTERP):
            raise ValueError('Binary must be statically linked with no interpreter or dynamic loader')
        if p_type != PT_LOAD:
            continue
        load_count += 1
        if p_align < ALIGNMENT or p_align & (p_align - 1):
            raise ValueError('PT_LOAD segment alignment must be a power of 2 >= 16 KiB')
        if p_vaddr % ALIGNMENT != p_offset % ALIGNMENT:
            raise ValueError('PT_LOAD virtual/file addresses violate 16-KiB congruence')
        if p_offset + p_filesz > len(data) or p_memsz < p_filesz:
            raise ValueError('PT_LOAD segment exceeds file or has invalid size')
    if not load_count:
        raise ValueError('No loadable ELF segments')
    return {'arch': 'AArch64', 'static': True, 'pt_load_count': load_count,
            'min_pt_load_alignment': ALIGNMENT, 'device_boot_verified': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    args = parser.parse_args()
    result = inspect_elf(args.binary.read_bytes())
    print(f'HOST_ONLY_ARM64_STATIC_ELF_OK: {result["pt_load_count"]} PT_LOAD segments aligned for 16 KiB')


if __name__ == '__main__':
    main()
