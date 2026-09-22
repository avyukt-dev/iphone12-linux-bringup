#!/usr/bin/env python3
"""Host-only full-system AArch64 Linux boot smoke test on QEMU 'virt'.

Uses Debian's official ARM64 installer kernel as a generic QEMU-virt kernel.
Does not emulate Apple's A14 or exercise an iPhone's bootloader/drivers.
Downloads/verifies the netboot kernel against Debian's same-release
SHA256SUMS, records its hash, and sends one command to our /dev/console shell.
"""
import argparse
import hashlib
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time
from urllib.request import urlopen

BASE = 'https://deb.debian.org/debian/dists/bookworm/main/installer-arm64/current/images/'
REL_KERNEL = './netboot/debian-installer/arm64/linux'
SHA_URL = BASE + 'SHA256SUMS'
KERNEL_URL = BASE + REL_KERNEL.removeprefix('./')
MARKER = 'QEMU_SYSTEM_ARM64_SHELL_OK'


def checksum_from_manifest(manifest: str) -> str:
    matches = []
    for line in manifest.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == REL_KERNEL:
            digest = parts[0].lower()
            if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('Invalid SHA-256 entry for the Debian ARM64 kernel')
            matches.append(digest)
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one matching kernel checksum, got {len(matches)}')
    return matches[0]


def acquire_kernel(path: Path) -> str:
    with urlopen(SHA_URL, timeout=30) as remote:
        manifest = remote.read(512 * 1024).decode('ascii')
    expected = checksum_from_manifest(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
        return expected
    temp = path.with_suffix('.part')
    try:
        with urlopen(KERNEL_URL, timeout=90) as remote, temp.open('wb') as dest:
            total = 0
            while True:
                chunk = remote.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    raise ValueError('Kernel download exceeds expected maximum size')
                dest.write(chunk)
        actual = hashlib.sha256(temp.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Debian kernel checksum mismatch: expected {expected}, got {actual}')
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return expected


def run_vm(kernel: Path, initramfs: Path, timeout: float) -> str:
    if not shutil.which('qemu-system-aarch64'):
        raise RuntimeError('Install qemu-system-arm for qemu-system-aarch64')
    if not kernel.is_file() or not initramfs.is_file():
        raise FileNotFoundError('Generic ARM64 kernel and local initramfs are both required')
    cmd = [
        'qemu-system-aarch64', '-machine', 'virt', '-cpu', 'cortex-a72',
        '-smp', '2', '-m', '768M', '-display', 'none', '-serial', 'stdio',
        '-monitor', 'none', '-no-reboot', '-nic', 'none',
        '-kernel', str(kernel.resolve()), '-initrd', str(initramfs.resolve()),
        '-append', 'console=ttyAMA0 rdinit=/init loglevel=5',
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, bufsize=0, start_new_session=True)
    log = bytearray()
    command_sent = False
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            if proc.stdout is None or proc.stdin is None:
                raise RuntimeError('QEMU stdio pipes not created')
            ready, _, _ = select.select([proc.stdout], [], [], 0.25)
            if ready:
                chunk = os.read(proc.stdout.fileno(), 8192)
                if not chunk:
                    raise RuntimeError(f'QEMU exited before shell command; exit={proc.poll()}')
                log.extend(chunk)
                if len(log) > 2 * 1024 * 1024:
                    del log[:len(log) - 1024 * 1024]
                text = log.decode('utf-8', errors='replace')
                if (not command_sent and
                        'early-init: launching interactive /dev/console shell' in text):
                    # Do not rely on terminal prompt formatting or boot timing.
                    proc.stdin.write(b'echo ' + MARKER.encode('ascii') + b'\n')
                    proc.stdin.flush()
                    command_sent = True
                if command_sent and (('\n' + MARKER + '\r') in text or
                                     ('\n' + MARKER + '\n') in text):
                    print('QEMU_SYSTEM_ARM64_REAL_KERNEL_BOOT_OK')
                    print(MARKER)
                    return text
            if proc.poll() is not None:
                raise RuntimeError(f'QEMU exited before shell marker; exit={proc.returncode}')
        raise TimeoutError('QEMU did not confirm an interactive shell before the deadline')
    except Exception:
        print('QEMU generic ARM64 guest diagnostic tail (not an iPhone log):',
              file=sys.stderr)
        print(log[-12000:].decode('utf-8', errors='replace'), file=sys.stderr)
        raise
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate(timeout=4)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--initramfs', type=Path,
                   default=Path('build/headless/early-initramfs.cpio.gz'))
    p.add_argument('--kernel', type=Path,
                   default=Path('build/qemu-system/debian-arm64-linux'))
    p.add_argument('--timeout', type=float, default=100)
    args = p.parse_args()
    if not args.initramfs.is_file():
        p.error(f'Missing userspace image: {args.initramfs} (build with BusyBox first)')
    digest = acquire_kernel(args.kernel)
    print(f'Debian ARM64 generic-virt kernel SHA-256: {digest}', flush=True)
    run_vm(args.kernel, args.initramfs, args.timeout)


if __name__ == '__main__':
    main()
