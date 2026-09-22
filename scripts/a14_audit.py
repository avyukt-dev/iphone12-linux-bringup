#!/usr/bin/env python3
"""Offline inventory of declared Apple device trees in a Linux source tree.

This checks source declarations only. It is NOT an exploit, driver test,
hardware compatibility certification, or evidence of an A14 Linux boot.
"""
import argparse
import json
from pathlib import Path
import re
import sys

DTB_RE = re.compile(
    r'^\s*dtb-\$\(CONFIG_ARCH_APPLE\)\s*\+=\s*([A-Za-z0-9_-]+)\.dtb\s*$',
    re.MULTILINE,
)


def inspect(kernel: Path, m1n1: Path, soc: str, board: str | None) -> dict:
    makefile = kernel / 'arch/arm64/boot/dts/apple/Makefile'
    if not makefile.is_file():
        raise FileNotFoundError(f'Apple DTB Makefile not found: {makefile}')
    names = DTB_RE.findall(makefile.read_text(encoding='utf-8'))
    matching = sorted(name for name in names if name.startswith(f'{soc}-'))
    board_match = None if board is None else f'{soc}-{board}' in names
    return {
        'soc': soc,
        'board': board,
        'apple_dtbs_declared': len(names),
        'soc_dtbs_declared': matching,
        'board_dtb_declared': board_match,
        'm1n1_source_present': (m1n1 / 'Makefile').is_file() and (m1n1 / 'src').is_dir(),
        'device_boot_verified': False,
        'meaning': 'Source inventory only; A14 boot and hardware compatibility are unverified.',
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel', type=Path, default=Path('vendor/linux'))
    parser.add_argument('--m1n1', type=Path, default=Path('vendor/m1n1'))
    parser.add_argument('--soc', default='t8101', help='Apple A14 SoC code')
    parser.add_argument('--board', help='Confirmed exact board code (do not guess)')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = inspect(args.kernel, args.m1n1, args.soc.lower(), args.board.lower() if args.board else None)
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f'SoC: {result["soc"]} | declared DTBs: {result["soc_dtbs_declared"]}')
        print(f'Exact board DTB declared: {result["board_dtb_declared"]}')
        print(f'm1n1 sources present: {result["m1n1_source_present"]}')
        print('On-device boot verified: NO (this tool cannot establish it)')
    # A candidate device tree is NOT evidence that booting is possible.
    return 2 if not result['soc_dtbs_declared'] or result['board_dtb_declared'] is False else 0


if __name__ == '__main__':
    sys.exit(main())
