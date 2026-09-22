#!/usr/bin/env python3
"""Host-only full-system ARM64 QEMU virt network + HTTP integration smoke test.

QEMU virt is NOT Apple A14. Slirp is restricted and forwards one host
loopback port to a guest. No phone or physical hardware is accessed.
"""
import argparse
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib import error, request

from test_qemu_arm64_system import acquire_kernel

PAGE = b'A14 Linux host-built userspace test page\n'


def run_vm_network(kernel: Path, initramfs: Path, timeout: float = 100) -> None:
    if not shutil.which('qemu-system-aarch64'):
        raise RuntimeError('qemu-system-aarch64 is required (Ubuntu: qemu-system-arm)')
    if not initramfs.is_file() or not kernel.is_file():
        raise FileNotFoundError('Need the generic ARM64 kernel and the BusyBox-enabled initramfs')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        host_port = s.getsockname()[1]

    cmd = [
        'qemu-system-aarch64', '-machine', 'virt', '-cpu', 'cortex-a72',
        '-smp', '2', '-m', '768M', '-display', 'none',
        '-serial', 'stdio', '-monitor', 'none', '-no-reboot',
        '-kernel', str(kernel.resolve()), '-initrd', str(initramfs.resolve()),
        '-append', 'console=ttyAMA0 rdinit=/init loglevel=5',
        '-netdev', f'user,id=n0,restrict=on,hostfwd=tcp:127.0.0.1:{host_port}-:8080',
        '-device', 'virtio-net-pci,netdev=n0',
    ]
    process = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, bufsize=0, start_new_session=True,
    )
    output = bytearray()
    configured = False
    deadline = time.monotonic() + timeout
    next_request = 0.
    try:
        while time.monotonic() < deadline:
            if process.stdin is None or process.stdout is None:
                raise RuntimeError('QEMU console pipes unavailable')
            ready, _, _ = select.select([process.stdout], [], [], 0.2)
            if ready:
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    raise RuntimeError(f'QEMU exited before serving HTTP: {process.poll()}')
                output.extend(chunk)
                if len(output) > 2 * 1024 * 1024:
                    del output[:len(output) - 1024 * 1024]
                text = output.decode('utf-8', errors='replace')
                if not configured and 'early-init: launching interactive /dev/console shell' in text:
                    commands = (
                        'ip link show eth0\n'
                        'ip link set eth0 up\n'
                        'ip addr add 10.0.2.15/24 dev eth0\n'
                        'httpd -p 8080 -h /www\n'
                        'echo QEMU_VIRT_HTTP_START_ATTEMPTED\n'
                    )
                    process.stdin.write(commands.encode('ascii'))
                    process.stdin.flush()
                    configured = True

            if process.poll() is not None:
                raise RuntimeError(f'QEMU exited before serving HTTP: {process.returncode}')
            if configured and time.monotonic() >= next_request:
                next_request = time.monotonic() + 0.3
                try:
                    with request.urlopen(f'http://127.0.0.1:{host_port}/', timeout=0.5) as response:
                        data = response.read(4096)
                        if response.status != 200 or data != PAGE:
                            raise RuntimeError(f'Unexpected guest HTTP response: {response.status}, {data!r}')
                        print('QEMU_SYSTEM_ARM64_VIRT_NETWORK_HTTP_OK', flush=True)
                        return
                except (error.URLError, TimeoutError, OSError):
                    pass
        raise TimeoutError('Guest ARM64 HTTP server did not respond over isolated virtio NIC')
    except Exception:
        print('QEMU generic ARM64 guest network diagnostics (NOT iPhone logs):', file=sys.stderr)
        print(output[-16000:].decode('utf-8', errors='replace'), file=sys.stderr)
        raise
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=4)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--initramfs', type=Path,
                   default=Path('build/headless/early-initramfs.cpio.gz'))
    p.add_argument('--kernel', type=Path, default=Path('build/qemu-system/debian-arm64-linux'))
    p.add_argument('--timeout', type=float, default=100)
    args = p.parse_args()
    if not args.initramfs.is_file():
        p.error('Build BusyBox-enabled initramfs before starting generic ARM64 VM')
    digest = acquire_kernel(args.kernel)
    print(f'Generic ARM64 VM Debian kernel SHA-256: {digest}', flush=True)
    run_vm_network(args.kernel, args.initramfs, timeout=args.timeout)


if __name__ == '__main__':
    main()
