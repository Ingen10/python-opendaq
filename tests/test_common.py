import unittest
from opendaq.common import crc, check_crc, CRCError, bytes2hex, mkcmd, escape_bytes


class TestCommon(unittest.TestCase):
    def test_crc(self):
        assert crc(bytearray([97])) == bytearray([0x00, 0x61])
        assert crc(bytearray([0xff, 0xff])) == bytearray([0x01, 0xfe])
        assert crc(bytearray('abcdefg', 'ascii')) == bytearray([0x02, 0xbc])
        assert crc(bytearray([0xff]*300)) == bytearray([0x2a, 0xd4])

    def test_check_crc(self):
        packets = [
            bytearray([0x00, 0x61, 0x61]),
            bytearray([0x02, 0xbc, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67]),
        ]

        for packet in packets:
            assert check_crc(packet) == packet[2:]

        self.assertRaises(CRCError, check_crc, bytearray([0x00, 0x61, 0x62]))

    def test_bytes2hex(self):
        array = bytearray([0x12, 0x34, 0x56])
        assert bytes2hex(array) == '12 34 56'

    def test_mkcmd(self):
        assert bytes2hex(mkcmd(160, '')) == '00 a0 a0 00'
        assert bytes2hex(mkcmd(18, 'b', 1)) == '00 14 12 01 01'
        assert bytes2hex(mkcmd(100, 'bH', 32, 1000)) == '01 72 64 03 20 03 e8'

    def test_escape_bytes(self):
        a = bytearray([0xff, 0x00, 0x7e, 0x34, 0x89, 0x7d, 0xaa])
        b = bytearray([0xff, 0x00, 0x14, 0x89, 0x8a])
        assert escape_bytes(a, (0x7e, 0x7d)) == b
