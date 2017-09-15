#!/usr/bin/env python

# Copyright 2013
# Ingen10 Ingenieria SL
#
# This file is part of opendaq.
#
# opendaq is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# opendaq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with opendaq.  If not, see <http://www.gnu.org/licenses/>.

import struct
import array


class CRCError(ValueError):
    pass


class LengthError(ValueError):
    pass


def crc(data):
    """Calculate the cyclic redundancy check of a data packet.

    :param data: Bynary data.
    """
    s = sum(bytearray(data)) % 65536
    return struct.pack('!H', s)


def check_crc(data):
    """Check the CRC of a data packet.

    :param data: Data packet to be validated.
    :returns: Packet payload.
    :raises: CRCError: Checksum was incorrect.
    """
    csum = data[:2]
    payload = data[2:]
    if csum != crc(payload):
        raise CRCError
    return payload


def check_stream_crc(head, data):
    """Cyclic redundancy check for stream packets.

    :param head: Header data of a packet.
    :param data: Payload of a packet.
    """
    csum = (head[0] << 8) + head[1]
    return csum == sum(head[2:] + data)


def mkcmd(ncmd, fmt, *args):
    """Make a command packet.

    :param ncmd: Command number.
    :param fmt: Format string, excluding header (in 'struct' notation).
    :param args: Command arguments.
    """
    fmt = '!BB' + fmt
    cmdlen = struct.calcsize(fmt) - 2
    cmd = struct.pack(fmt, ncmd, cmdlen, *args)
    return bytearray(crc(cmd) + cmd)


def bytes2hex(data):
    """Hexdump binary data."""
    hexstr = ["%02x" % c for c in data]
    return ' '.join(hexstr)


NAK = mkcmd(160, '')

def parse_command(data, fmt, length):
    if data == NAK:
        raise IOError("NAK response received")

    if len(data) != length:
        raise LengthError("Bad packet length %d (it should be %d)" %
                          (len(data), length))

    data = struct.unpack(fmt, check_crc(data))
    if data[1] != length - 4:
        raise LengthError("Bad body length %d (it should be %d)" %
                          (length - 4, data[1]))
    # Strip 'command' and 'length' values from returned data
    return data[2:]


def escape_bytes(data, escape_codes):
    newdata = bytearray()
    escape = False

    for b in data:
        if b in escape_codes:
            escape = True
        elif escape:
            newdata.append(b ^ 0x20)
            escape = False
        else:
            newdata.append(b)

    return newdata
