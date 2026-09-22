import gzip
import importlib.util
from pathlib import Path
import stat
import struct
import unittest


def load_script(name):
    path = Path(__file__).resolve().parents[1] / 'scripts' / name
    spec = importlib.util.spec_from_file_location(name.removesuffix('.py'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packer = load_script('make_initramfs.py')
verifier = load_script('verify_arm64_elf.py')


def fake_arm64_elf():
    """Minimal syntactically valid ELF for parser tests, NOT executable code."""
    data = bytearray(0x4004)
    data[:4] = b'\x7fELF'
    data[4:7] = (2, 1, 1)
    struct.pack_into('<HH', data, 16, 2, 183)
    struct.pack_into('<Q', data, 32, 64)
    struct.pack_into('<HH', data, 54, 56, 1)
    struct.pack_into('<IIQQQQQQ', data, 64, 1, 5, 0x4000,
                     0x4000, 0, 4, 4, 0x4000)
    data[0x4000:0x4004] = b'TEST'
    return bytes(data)


def decode_newc(raw):
    index = 0
    entries = {}
    while index < len(raw):
        if raw[index:index + 6] != b'070701':
            raise AssertionError('invalid newc magic')
        fields = [int(raw[index + 6 + 8 * i:index + 14 + 8 * i], 16)
                  for i in range(13)]
        start = index + 110
        namesize = fields[11]
        name = raw[start:start + namesize - 1].decode('ascii')
        data_start = (start + namesize + 3) & ~3
        payload = raw[data_start:data_start + fields[6]]
        entries[name] = {'mode': fields[1], 'major': fields[9],
                         'minor': fields[10], 'payload': payload}
        index = (data_start + fields[6] + 3) & ~3
        if name == 'TRAILER!!!':
            break
    return entries


class EarlyInitramfsTests(unittest.TestCase):
    def test_packer_rejects_non_arm64(self):
        blob = bytearray(fake_arm64_elf())
        struct.pack_into('<H', blob, 18, 62)  # x86-64
        with self.assertRaisesRegex(ValueError, 'AArch64'):
            packer.build_cpio(bytes(blob))

    def test_packer_rejects_short_header(self):
        with self.assertRaises(ValueError):
            packer.build_cpio(b'\x7fELF')

    def test_reproducible_gzip(self):
        elf = fake_arm64_elf()
        self.assertEqual(packer.build_gzip(elf), packer.build_gzip(elf))

    def test_init_and_console_exist_with_expected_types(self):
        elf = fake_arm64_elf()
        entries = decode_newc(gzip.decompress(packer.build_gzip(elf)))
        self.assertEqual(entries['init']['payload'], elf)
        self.assertTrue(stat.S_ISREG(entries['init']['mode']))
        self.assertEqual(entries['init']['mode'] & 0o777, 0o755)
        self.assertTrue(stat.S_ISCHR(entries['dev/console']['mode']))
        self.assertEqual((entries['dev/console']['major'],
                          entries['dev/console']['minor']), (5, 1))
        self.assertTrue(stat.S_ISDIR(entries['proc']['mode']))
        self.assertIn('TRAILER!!!', entries)
        self.assertNotIn('bin/sh', entries)

    def test_optional_busybox_shell_and_httpd_entries(self):
        elf = fake_arm64_elf()
        entries = decode_newc(gzip.decompress(packer.build_gzip(elf, elf)))
        self.assertEqual(entries['bin/busybox']['payload'], elf)
        self.assertTrue(stat.S_ISREG(entries['bin/busybox']['mode']))
        for name in ('sh', 'httpd', 'ip', 'ls', 'mount'):
            self.assertTrue(stat.S_ISLNK(entries[f'bin/{name}']['mode']))
            self.assertEqual(entries[f'bin/{name}']['payload'], b'busybox')
        self.assertIn('www/index.html', entries)
        self.assertFalse(verifier.inspect_elf(elf)['device_boot_verified'])

    def test_busybox_must_have_arm64_elf_header(self):
        with self.assertRaises(ValueError):
            packer.build_cpio(fake_arm64_elf(), b'not an ELF binary')

    def test_optional_busybox_archive_remains_deterministic(self):
        elf = fake_arm64_elf()
        self.assertEqual(packer.build_gzip(elf, elf), packer.build_gzip(elf, elf))

    def test_elf_validator_accepts_minimal_header(self):
        facts = verifier.inspect_elf(fake_arm64_elf())
        self.assertTrue(facts['static'])
        self.assertFalse(facts['device_boot_verified'])
        self.assertEqual(facts['pt_load_count'], 1)

    def test_elf_validator_rejects_4k_segment_alignment(self):
        elf = bytearray(fake_arm64_elf())
        struct.pack_into('<Q', elf, 64 + 48, 4096)
        with self.assertRaisesRegex(ValueError, '16 KiB'):
            verifier.inspect_elf(bytes(elf))

    def test_elf_validator_rejects_dynamic_linker(self):
        elf = bytearray(fake_arm64_elf())
        struct.pack_into('<I', elf, 64, verifier.PT_INTERP)
        with self.assertRaisesRegex(ValueError, 'statically linked'):
            verifier.inspect_elf(bytes(elf))

    def test_elf_validator_rejects_wrong_machine(self):
        elf = bytearray(fake_arm64_elf())
        struct.pack_into('<H', elf, 18, 62)
        with self.assertRaisesRegex(ValueError, 'AArch64'):
            verifier.inspect_elf(bytes(elf))

    def test_elf_validator_rejects_invalid_segment_extent(self):
        elf = bytearray(fake_arm64_elf())
        struct.pack_into('<Q', elf, 64 + 32, len(elf) + 8)
        with self.assertRaisesRegex(ValueError, 'segment'):
            verifier.inspect_elf(bytes(elf))


if __name__ == '__main__':
    unittest.main()
