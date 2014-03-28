import unittest
from opendaq.common import crc, check_crc, CRCError, str2hex, mkcmd


class TestCommon(unittest.TestCase):
    def test_crc(self):
        assert crc('a') == '\x00\x61'
        assert crc('\xff\xff') == '\x01\xfe'
        assert crc('abcdefg') == '\x02\xbc'
        assert crc('\xff'*300) == '\x2a\xd4'

    def test_check_crc(self):
        assert check_crc('\x00\x61' + 'a') == 'a'
        assert check_crc('\x02\xbc' + 'abcdefg') == 'abcdefg'

        self.assertRaises(CRCError, check_crc, '\x00a' + 'b')

    def test_str2hex(self):
        assert str2hex('\x12\x34\x56') == '12 34 56'

    def test_mkcmd(self):
        assert str2hex(mkcmd(160, '')) == '00 a0 a0 00'
        assert str2hex(mkcmd(18, 'b', 1)) == '00 14 12 01 01'
        assert str2hex(mkcmd(100, 'bH', 32, 1000)) == '01 72 64 03 20 03 e8'
