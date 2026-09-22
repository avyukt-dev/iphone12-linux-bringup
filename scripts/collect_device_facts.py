#!/usr/bin/env python3
"""Read a minimal, allowlisted set of non-unique iPhone identity/firmware facts.

Requires a USB-connected, already trusted/paired iPhone and libimobiledevice's
ideviceinfo tool on the host. Does not call jailbreak, restore or flash tools.
Never query/print UDID, serial number, ECID, Wi-Fi/Bluetooth addresses, or the
unfiltered ideviceinfo output.
"""
import json
import re
import shutil
import subprocess
import sys

FIELDS = {
    'ProductType': re.compile(r'iPhone[0-9]+,[0-9]+'),
    'HardwareModel': re.compile(r'[A-Za-z0-9]+AP'),
    'ProductVersion': re.compile(r'[0-9]+(?:\.[0-9]+){0,2}'),
    'BuildVersion': re.compile(r'[A-Za-z0-9]{3,16}'),
}
TARGET_PRODUCT_TYPE = 'iPhone13,2'


def clean_value(key: str, stdout: str) -> str | None:
    """Accept only a single line matching the allowlisted value's syntax."""
    value = stdout.strip()
    if value.startswith(key + ':'):
        value = value[len(key) + 1:].strip()
    if '\n' in value or '\r' in value:
        return None
    return value if FIELDS[key].fullmatch(value) else None


def collect(run=subprocess.run) -> dict:
    """Read four specific keys using -s to avoid automatic pairing.

    The caller should ensure exactly one iPhone is connected to USB.
    Raw stdout/stderr are never logged; failures use fixed diagnostic strings.
    """
    facts = {}
    statuses = {}
    for key in FIELDS:
        try:
            proc = run(['ideviceinfo', '-s', '-k', key],
                       capture_output=True, text=True, timeout=10, check=False)
        except subprocess.TimeoutExpired:
            statuses[key] = 'timeout'
            continue
        except OSError:
            statuses[key] = 'tool_unavailable'
            continue
        if proc.returncode != 0:
            statuses[key] = 'device_query_failed'
            continue
        value = clean_value(key, proc.stdout)
        if value is None:
            statuses[key] = 'missing_or_invalid_value'
            continue
        facts[key] = value
        statuses[key] = 'ok'
    return {
        'device_facts': facts,
        'field_status': statuses,
        'target_product_type_verified': facts.get('ProductType') == TARGET_PRODUCT_TYPE,
        'source': 'USB-connected device via ideviceinfo -s -k (read-only)',
        'boot_chain_verified': False,
        'native_linux_boot_verified': False,
    }


def main() -> int:
    if not shutil.which('ideviceinfo'):
        print('ideviceinfo not installed; install libimobiledevice-utils on the Linux host.',
              file=sys.stderr)
        return 3
    result = collect()
    print(json.dumps(result, indent=2, sort_keys=True))
    # Exit 2: one or more facts missing or connected device is not iPhone 12.
    return 0 if result['target_product_type_verified'] and all(
        status == 'ok' for status in result['field_status'].values()
    ) else 2


if __name__ == '__main__':
    sys.exit(main())
