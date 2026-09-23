import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'scripts' / 'triage_boot_entries.py'
spec = importlib.util.spec_from_file_location('triage_boot_entries', PATH)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class BootEntryTriageTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(
            (ROOT / 'research' / 'boot-entry-candidates.json').read_text(encoding='utf-8')
        )

    def statuses(self):
        return {item['candidate']: item['paper_scope_status']
                for item in tool.triage(self.data)['assessments']}

    def test_current_target_does_not_match_published_entry(self):
        result = tool.triage(self.data)
        self.assertFalse(result['actual_device_boot_verified'])
        self.assertFalse(result['hardware_test_approved'])
        self.assertEqual(self.statuses(), {
            'checkm8-hoolock-pongo': 'soc_out_of_scope',
            'usbliter8-a14-a0-b0': 'hardware_class_out_of_scope',
            'm1n1-chainloader': 'not_an_entry_method',
        })
        self.assertIsNone(result['target']['bootrom_build'])

    def test_ios_build_is_not_bootrom_revision(self):
        self.assertEqual(self.data['target']['ios_build'], '24A437')
        self.assertIsNone(self.data['target']['bootrom_build'])

    def test_prototype_method_with_unknown_rom_still_needs_evidence(self):
        self.data['target']['hardware_class'] = 'preproduction'
        self.assertEqual(self.statuses()['usbliter8-a14-a0-b0'],
                         'requires_bootrom_revision_evidence')

    def test_known_production_rom_is_explicitly_excluded(self):
        self.data['target']['hardware_class'] = 'preproduction'
        self.data['target']['bootrom_build'] = '5281.0.0.100.45'
        self.assertEqual(self.statuses()['usbliter8-a14-a0-b0'],
                         'bootrom_explicitly_excluded')

    def test_matching_prototype_rom_is_still_not_real_boot_proof(self):
        self.data['target']['hardware_class'] = 'preproduction'
        self.data['target']['bootrom_build'] = '5281.0.0.100.22'
        result = tool.triage(self.data)
        record = next(x for x in result['assessments']
                      if x['candidate'] == 'usbliter8-a14-a0-b0')
        self.assertEqual(record['paper_scope_status'],
                         'paper_scope_only_needs_real_boot_and_recovery_evidence')
        self.assertFalse(result['actual_device_boot_verified'])
        self.assertFalse(result['hardware_test_approved'])

    def test_wrong_rom_build_cannot_match_prototype_candidate(self):
        self.data['target']['hardware_class'] = 'preproduction'
        self.data['target']['bootrom_build'] = '5281.0.0.100.99'
        self.assertEqual(self.statuses()['usbliter8-a14-a0-b0'], 'bootrom_out_of_scope')

    def test_m1n1_never_becomes_independent_entry_by_soc_match(self):
        self.data['target']['hardware_class'] = 'preproduction'
        self.data['target']['bootrom_build'] = '5281.0.0.100.22'
        self.assertEqual(self.statuses()['m1n1-chainloader'], 'not_an_entry_method')

    def test_malformed_inventory_rejected(self):
        data = copy.deepcopy(self.data)
        data['candidates'][0]['independent_entry'] = 'yes'
        with self.assertRaisesRegex(ValueError, 'independent_entry'):
            tool.triage(data)

    def test_duplicate_candidate_rejected(self):
        data = copy.deepcopy(self.data)
        data['candidates'].append(copy.deepcopy(data['candidates'][0]))
        with self.assertRaisesRegex(ValueError, 'distinct'):
            tool.triage(data)

    def test_missing_source_url_rejected(self):
        data = copy.deepcopy(self.data)
        data['candidates'][0]['source_url'] = ''
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            tool.triage(data)


if __name__ == '__main__':
    unittest.main()
