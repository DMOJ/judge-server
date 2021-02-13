import os
import sys
import unittest

from dmoj.cptbox.utils import MemoryIO

TEST_DATA = b'Hello, World!'


class TestMemoryIO(unittest.TestCase):
    def test_read_back(self):
        with MemoryIO() as f:
            f.write(TEST_DATA)
            f.seek(0, os.SEEK_SET)
            self.assertEqual(f.read(), TEST_DATA)

    @unittest.skipIf(sys.platform.startswith('freebsd'), 'Sealing not supported on FreeBSD')
    def test_seal(self):
        with MemoryIO() as f:
            f.write(TEST_DATA)
            f.seal()

            f.seek(0, os.SEEK_SET)
            self.assertEqual(f.read(), TEST_DATA)

            with self.assertRaises(IOError):
                f.write(TEST_DATA)

            with self.assertRaises(IOError):
                f.truncate(0)
