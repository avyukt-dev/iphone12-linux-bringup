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

    def write_dtb(self, text):
        (self.dts / 'Makefile').write_text(text)

    def test_no_a14_entry_does_not_imply_boot(self):
        self.write_dtb('dtb-$(CONFIG_ARCH_APPLE) += t8103-j274.dtb\n')
        result = audit.inspect(self.kernel, self.m1n1)
        self.assertEqual(result['soc_dtb_declarations'], [])
        self.assertFalse(result['boot_chain_verified'])
        self.assertFalse(result['on_device_boot_verified'])
        self.assertEqual(result['hardware_reference']['board_config'], 'D53gAP')

    def test_declaration_without_dts_file_is_not_a_valid_candidate(self):
        self.write_dtb('dtb-$(CONFIG_ARCH_APPLE) += t8101-example.dtb\n')
        result = audit.inspect(self.kernel, self.m1n1, board='example')
        self.assertFalse(result['soc_dts_files_present']['t8101-example'])
        self.assertFalse(result['requested_dtb_declared_with_source'])

    def test_candidate_source_still_does_not_establish_boot(self):
        self.write_dtb('dtb-$(CONFIG_ARCH_APPLE) += t8101-example.dtb # comment\n')
        (self.dts / 't8101-example.dts').write_text('/dts-v1/;\n')
        result = audit.inspect(self.kernel, self.m1n1, board='example')
        self.assertTrue(result['requested_dtb_declared_with_source'])
        self.assertFalse(result['boot_chain_verified'])
        self.assertFalse(result['on_device_boot_verified'])

    def test_wrong_board_is_not_marked_supported(self):
        self.write_dtb('dtb-$(CONFIG_ARCH_APPLE) += t8101-other.dtb\n')
        (self.dts / 't8101-other.dts').write_text('/dts-v1/;\n')
        self.assertFalse(audit.inspect(self.kernel, self.m1n1, board='example')['requested_dtb_declared_with_source'])

    def test_missing_makefile_is_error(self):
        with self.assertRaises(FileNotFoundError):
            audit.inspect(self.kernel, self.m1n1)

    def test_invalid_board_suffix_rejected(self):
        self.write_dtb('dtb-$(CONFIG_ARCH_APPLE) += t8101-example.dtb\n')
        with self.assertRaises(ValueError):
            audit.inspect(self.kernel, self.m1n1, board='../escape')

    def test_undeclared_dts_not_a_candidate(self):
        self.write_dtb('dtb-$(CONFIG_ARCH_APPLE) += t8103-j274.dtb\n')
        (self.dts / 't8101-example.dts').write_text('/dts-v1/;\n')
        self.assertEqual(audit.inspect(self.kernel, self.m1n1)['soc_dtb_declarations'], [])

    def test_missing_m1n1_checkout_does_not_crash(self):
        self.write_dtb('dtb-$(CONFIG_ARCH_APPLE) += t8103-j274.dtb\n')
        self.assertFalse(audit.inspect(self.kernel, self.root / 'nope')['m1n1_source_checkout_present'])


if __name__ == '__main__':
    unittest.main()
