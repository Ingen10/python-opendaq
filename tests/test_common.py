import pytest
from opendaq.common import crc, check_crc, CRCError, str2hex, mkcmd


def test_crc():
    assert crc('a') == '\x00\x61'
    assert crc('\xff\xff') == '\x01\xfe'
    assert crc('abcdefg') == '\x02\xbc'
    assert crc('\xff'*300) == '\x2a\xd4'


def test_check_crc():
    assert check_crc('\x00\x61' + 'a') == 'a'
    assert check_crc('\x02\xbc' + 'abcdefg') == 'abcdefg'

    with pytest.raises(CRCError):
        check_crc('\x00a' + 'b')


def test_mkcmd():
    assert str2hex(mkcmd(18, 'b', 1)) == '00 14 12 01 01'
    assert str2hex(mkcmd(100, 'bH', 32, 1000)) == '01 73 64 04 20 03 e8'
