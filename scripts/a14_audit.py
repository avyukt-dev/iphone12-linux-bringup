#!/usr/bin/env python3
"""Inspect source declarations, not actual A14 boot or hardware compatibility."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

DTB_RE = re.compile(
    r'^\s*dtb-\$\(CONFIG_ARCH_APPLE\)\s*\+=\s*([A-Za-z0-9_-]+)\.dtb\s*(?:#.*)?$',
    re.MULTILINE,
)
SOC = 't8101'
MODEL = 'iPhone13,2'
BOARD_CONFIG = 'D53gAP'


def git_head(root: Path):
    if not (root / '.git').exists():
        return None
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                            text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def inspect(kernel: Path, m1n1: Path, soc: str = SOC, board: str | None = None) -> dict:
    """Return evidence for matching DTBs; board is a *verified DTB suffix*, not BoardConfig."""
    root = kernel / 'arch/arm64/boot/dts/apple'
    makefile = root / 'Makefile'
    if not makefile.is_file():
        raise FileNotFoundError(f'Apple DTB Makefile not found: {makefile}')
    if not re.fullmatch(r'[a-z0-9]+', soc):
        raise ValueError('SoC identifier must be alphanumeric and lowercase')
    if board is not None and not re.fullmatch(r'[a-z0-9_-]+', board):
        raise ValueError('DTB suffix must contain only lowercase letters, digits, underscores or hyphens')
    names = sorted(set(DTB_RE.findall(makefile.read_text(encoding='utf-8'))))
    matching = [name for name in names if name.startswith(f'{soc}-')]
    source_files = {name: (root / (name + '.dts')).is_file() for name in matching}
    requested = None if board is None else f'{soc}-{board}'
    present = None if requested is None else requested in matching and source_files[requested]
    return {
        'hardware_reference': {'model': MODEL, 'board_config': BOARD_CONFIG, 'soc': SOC},
        'inspected_soc': soc,
        'kernel_commit': git_head(kernel),
        'm1n1_commit': git_head(m1n1),
        'apple_dtb_declarations': len(names),
        'soc_dtb_declarations': matching,
        'soc_dts_files_present': source_files,
        'requested_dtb': requested,
        'requested_dtb_declared_with_source': present,
        'm1n1_source_checkout_present': (m1n1 / 'Makefile').is_file() and (m1n1 / 'src').is_dir(),
        'boot_chain_verified': False,
        'on_device_boot_verified': False,
        'scope': 'SOURCE INVENTORY ONLY. DTB declarations do not establish a supported driver, boot method, or actual device compatibility.',
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kernel', type=Path, default=Path('vendor/linux'))
    p.add_argument('--m1n1', type=Path, default=Path('vendor/m1n1'))
    p.add_argument('--soc', default=SOC)
    p.add_argument('--board', help='Verified DTB *filename suffix* (not Apple BoardConfig D53gAP)')
    p.add_argument('--json', action='store_true')
    args = p.parse_args(argv)
    try:
        result = inspect(args.kernel, args.m1n1, args.soc.lower(), args.board.lower() if args.board else None)
    except (OSError, UnicodeError, ValueError) as exc:
        p.error(str(exc))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f'Inspected SoC: {result["inspected_soc"]}; DTBs declared: {result["soc_dtb_declarations"]}')
        print(f'Kernel HEAD: {result["kernel_commit"]}; m1n1 HEAD: {result["m1n1_commit"]}')
        print('Boot chain and device execution: NOT VERIFIED')
    return 2 if not result['soc_dtb_declarations'] or any(not present for present in result['soc_dts_files_present'].values()) or result['requested_dtb_declared_with_source'] is False else 0


if __name__ == '__main__':
    sys.exit(main())
