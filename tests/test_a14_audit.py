import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'a14_audit.py'
spec = importlib.util.spec_from_file_location('a14_audit', SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.kernel = self.root / 'linux'
        self.dts = self.kernel / 'arch/arm64/boot/dts/apple'
        self.dts.mkdir(parents=True)
        self.m1n1 = self.root / 'm1n1'
        (self.m1n1 / 'src').mkdir(parents=True)
        (self.m1n1 / 'Makefile').write_text('all:\n\t@true\n')

    def test_absent_a14_is_reported_without_false_boot_claim(self):
        (self.dts / 'Makefile').write_text('dtb-$(CONFIG_ARCH_APPLE) += t8010-d10.dtb\n')
        result = audit.inspect(self.kernel, self.m1n1, 't8101', None)
        self.assertEqual(result['soc_dtbs_declared'], [])
        self.assertFalse(result['device_boot_verified'])

    def test_candidate_dtb_still_does_not_establish_boot(self):
        (self.dts / 'Makefile').write_text('dtb-$(CONFIG_ARCH_APPLE) += t8101-example.dtb\n')
        result = audit.inspect(self.kernel, self.m1n1, 't8101', 'example')
        self.assertEqual(result['soc_dtbs_declared'], ['t8101-example'])
        self.assertTrue(result['board_dtb_declared'])
        self.assertFalse(result['device_boot_verified'])

    def test_wrong_board_is_not_marked_supported(self):
        (self.dts / 'Makefile').write_text('dtb-$(CONFIG_ARCH_APPLE) += t8101-other.dtb\n')
        self.assertFalse(audit.inspect(self.kernel, self.m1n1, 't8101', 'example')['board_dtb_declared'])

    def test_missing_makefile_is_error(self):
        with self.assertRaises(FileNotFoundError):
            audit.inspect(self.kernel, self.m1n1, 't8101', None)


if __name__ == '__main__':
    unittest.main()
