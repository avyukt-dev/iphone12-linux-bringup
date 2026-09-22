#!/usr/bin/env python3
"""Smoke-test the ARM64 BusyBox HTTP applet in QEMU Linux user mode.

QEMU forwards syscalls to this HOST Linux kernel. This does not establish
iPhone hardware, USB/Wi-Fi, native Linux kernel boot, or A14 compatibility.
"""
import argparse
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib import error, request

PAGE = b'A14_HOST_ARM64_HTTPD_OK\n'


def smoke_test(binary: Path, *, timeout: float = 12.0) -> None:
    if not binary.is_file():
        raise FileNotFoundError(f'Missing ARM64 BusyBox executable: {binary}')
    # Let the OS select an unused port, release it immediately before launching
    # the server. This is a smoke test; retry bounded connection attempts.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]

    with tempfile.TemporaryDirectory(prefix='arm64-httpd-smoke-') as td:
        root = Path(td)
        (root / 'index.html').write_bytes(PAGE)
        command = [
            'qemu-aarch64', str(binary.resolve()),
            'httpd', '-f', '-p', f'127.0.0.1:{port}', '-h', str(root),
        ]
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + timeout
            last_error = 'no response'
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError('ARM64 HTTP applet exited before serving the test page')
                try:
                    with request.urlopen(f'http://127.0.0.1:{port}/', timeout=0.5) as response:
                        body = response.read(4096)
                        if response.status != 200 or body != PAGE:
                            raise RuntimeError(
                                f'Unexpected HTTP response: status={response.status}, body={body!r}'
                            )
                        print('A14_HOST_ARM64_HTTPD_OK')
                        return
                except (error.URLError, TimeoutError, OSError) as exc:
                    last_error = type(exc).__name__
                    time.sleep(0.15)
            raise TimeoutError(f'ARM64 HTTP applet did not serve a response: {last_error}')
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate(timeout=3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('busybox', type=Path)
    args = parser.parse_args()
    smoke_test(args.busybox)


if __name__ == '__main__':
    main()
