import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'test_qemu_arm64_system.py'
spec = importlib.util.spec_from_file_location('test_qemu_arm64_system', PATH)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class GenericArm64KernelManifestTests(unittest.TestCase):
    def test_one_exact_kernel_entry(self):
        digest = 'ab' * 32
        text = ('ff' * 32 + '  ./netboot/debian-installer/arm64/linux-extra\n'
                + digest + '  ./netboot/debian-installer/arm64/linux\n')
        self.assertEqual(tool.checksum_from_manifest(text), digest)

    def test_duplicate_match_is_rejected(self):
        line = ('ab' * 32) + '  ' + tool.REL_KERNEL
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            tool.checksum_from_manifest(line + '\n' + line)

    def test_missing_match_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            tool.checksum_from_manifest('ff' * 32 + '  ./unrelated/kernel')

    def test_invalid_sha256_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid SHA-256'):
            tool.checksum_from_manifest('not-a-hash  ' + tool.REL_KERNEL)

    def test_kernel_checksum_is_pinned_from_verified_ci_boot(self):
        self.assertEqual(tool.PINNED_KERNEL_SHA256,
                         '84b9c190bb4589c4a9527e3191fec051f9f115e88f0a3e8afae96ba0dfb4dfef')

    def test_marker_is_not_claim_of_iphone_execution(self):
        self.assertIn('QEMU_SYSTEM_', tool.MARKER)
        self.assertNotIn('IPHONE', tool.MARKER)


if __name__ == '__main__':
    unittest.main()
