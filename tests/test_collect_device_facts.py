import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'collect_device_facts.py'
spec = importlib.util.spec_from_file_location('collect_device_facts', SOURCE)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def device_run(values, errors=None):
    errors = errors or {}
    def run(argv, **kwargs):
        assert argv[:3] == ['ideviceinfo', '-s', '-k']
        assert set(argv[3:]).issubset(collector.FIELDS)
        assert kwargs.get('timeout') == 10
        key = argv[3]
        if key in errors:
            error = errors[key]
            if isinstance(error, Exception):
                raise error
            return Mock(returncode=error, stdout='', stderr='SERIAL-PRIVATE-DATA')
        return Mock(returncode=0, stdout=values[key], stderr='')
    return run


class DeviceFactsTests(unittest.TestCase):
    def setUp(self):
        self.values = dict(ProductType='iPhone13,2', HardwareModel='D53gAP',
                           ProductVersion='27.0', BuildVersion='24A123')

    def test_target_and_four_explicit_queries(self):
        result = collector.collect(run=device_run(self.values))
        self.assertTrue(result['target_product_type_verified'])
        self.assertEqual(result['device_facts'], self.values)
        self.assertFalse(result['boot_chain_verified'])
        self.assertFalse(result['native_linux_boot_verified'])

    def test_non_target_does_not_claim_target(self):
        values = dict(self.values, ProductType='iPhone13,3')
        result = collector.collect(run=device_run(values))
        self.assertFalse(result['target_product_type_verified'])

    def test_filter_multiline_and_sensitive_unfiltered_output(self):
        values = dict(self.values, ProductType='iPhone13,2\nUniqueDeviceID: SECRET')
        result = collector.collect(run=device_run(values))
        self.assertNotIn('ProductType', result['device_facts'])
        self.assertNotIn('SECRET', str(result))

    def test_missing_value_is_not_reported_as_verified(self):
        values = dict(self.values, HardwareModel='')
        result = collector.collect(run=device_run(values))
        self.assertEqual(result['field_status']['HardwareModel'], 'missing_or_invalid_value')
        self.assertNotIn('HardwareModel', result['device_facts'])

    def test_command_errors_hide_sensitive_stderr(self):
        result = collector.collect(run=device_run(self.values, {'BuildVersion': 1}))
        self.assertNotIn('BuildVersion', result['device_facts'])
        self.assertNotIn('SERIAL-PRIVATE-DATA', str(result))

    def test_timeouts_hide_device_log(self):
        result = collector.collect(run=device_run(self.values, {'BuildVersion': subprocess.TimeoutExpired('ideviceinfo', 10)}))
        self.assertEqual(result['field_status']['BuildVersion'], 'timeout')

    def test_key_prefixed_output_is_accepted(self):
        values = dict(self.values, ProductType='ProductType: iPhone13,2')
        self.assertTrue(collector.collect(run=device_run(values))['target_product_type_verified'])

    def test_arbitrary_private_output_is_rejected(self):
        values = dict(self.values, HardwareModel='UniqueDeviceID: SECRET')
        result = collector.collect(run=device_run(values))
        self.assertNotIn('SECRET', str(result))

    def test_unexpected_binary_is_handled_without_logging(self):
        result = collector.collect(run=device_run(self.values, {'ProductType': OSError('serial PRIVATE')}))
        self.assertEqual(result['field_status']['ProductType'], 'tool_unavailable')
        self.assertNotIn('PRIVATE', str(result))


if __name__ == '__main__':
    unittest.main()
