#!/usr/bin/env python3
"""Offline *paper-scope* triage of published boot-entry methods.

Never executes an exploit, queries any device, flashes firmware, or proves
that a method works. A method with matching labels still requires external,
device-specific boot-execution and recovery evidence before hardware testing.
"""
import argparse
import json
from pathlib import Path
import sys

DEFAULT_INVENTORY = Path(__file__).resolve().parents[1] / 'research' / 'boot-entry-candidates.json'


def validate_inventory(data: dict) -> None:
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Expected candidate inventory schema_version 1')
    target = data.get('target')
    if not isinstance(target, dict):
        raise ValueError('Target object is required')
    for field in ('product_type', 'board_config', 'soc', 'ios_version',
                  'ios_build', 'hardware_class'):
        if not isinstance(target.get(field), str) or not target[field].strip():
            raise ValueError(f'Target {field} must be a non-empty string')
    rom = target.get('bootrom_build')
    if rom is not None and (not isinstance(rom, str) or not rom.strip()):
        raise ValueError('bootrom_build must be null (unmeasured) or nonempty string')
    candidates = data.get('candidates')
    if not isinstance(candidates, list) or not candidates:
        raise ValueError('At least one candidate is required')
    seen = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError('Candidate must be an object')
        identifier = candidate.get('id')
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError('Candidate IDs must be distinct nonempty strings')
        seen.add(identifier)
        if not isinstance(candidate.get('source_url'), str) or not candidate['source_url'].startswith('https://'):
            raise ValueError(f'{identifier}: a HTTPS evidence URL is required')
        if type(candidate.get('independent_entry')) is not bool:
            raise ValueError(f'{identifier}: independent_entry must be boolean')
        for field in ('supported_socs', 'hardware_classes', 'supported_bootrom_builds',
                      'excluded_bootrom_builds'):
            value = candidate.get(field)
            if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
                raise ValueError(f'{identifier}: {field} must be a list of nonempty strings')


def triage(data: dict) -> dict:
    validate_inventory(data)
    t = data['target']
    assessed = []
    for c in data['candidates']:
        if not c['independent_entry']:
            status = 'not_an_entry_method'
        elif t['soc'] not in c['supported_socs']:
            status = 'soc_out_of_scope'
        elif t['hardware_class'] not in c['hardware_classes']:
            status = 'hardware_class_out_of_scope'
        elif t['bootrom_build'] is not None and t['bootrom_build'] in c['excluded_bootrom_builds']:
            status = 'bootrom_explicitly_excluded'
        elif c['supported_bootrom_builds'] and t['bootrom_build'] is None:
            status = 'requires_bootrom_revision_evidence'
        elif c['supported_bootrom_builds'] and t['bootrom_build'] not in c['supported_bootrom_builds']:
            status = 'bootrom_out_of_scope'
        else:
            status = 'paper_scope_only_needs_real_boot_and_recovery_evidence'
        assessed.append({'candidate': c['id'], 'paper_scope_status': status,
                         'source_url': c['source_url']})
    return {
        'target': {'product_type': t['product_type'], 'soc': t['soc'],
                   'board_config': t['board_config'], 'ios_build': t['ios_build'],
                   'hardware_class': t['hardware_class'],
                   'bootrom_build': t['bootrom_build']},
        'assessments': assessed,
        'actual_device_boot_verified': False,
        'hardware_test_approved': False,
        'scope': 'Document classification only. A match is not an exploit, proof of boot, or device test authorization.',
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory', type=Path, default=DEFAULT_INVENTORY)
    args = p.parse_args(argv)
    try:
        result = triage(json.loads(args.inventory.read_text(encoding='utf-8')))
    except (OSError, ValueError, TypeError) as exc:
        print(f'Invalid inventory: {exc}', file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, sort_keys=True))
    # 0 means successful OFFLINE RESEARCH TRIAGE ONLY, not A14 compatibility.
    return 0


if __name__ == '__main__':
    sys.exit(main())
