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

class CRCError(ValueError):
    pass


class LengthError(ValueError):
    pass


def crc(data):
    """Calculate cyclic redundancy check of a data package

    Args:
        data: Data package
    """
    s = sum((ord(c) for c in data)) % 65536
    return struct.pack('!H', s)


def check_crc(data):
    """Check data package checksum

    Args:
        data: Data package to be validated
    Raises:
        CRCError: Checksum was incorrect
    """
    csum = data[:2]
    payload = data[2:]
    if csum != crc(payload):
        raise CRCError
    return payload


def check_stream_crc(head, data):
    """
    Cyclic redundancy check for stream packets

    Args:
        head: header data of a packet
        data: payload of a packet
    """
    csum = (head[0] << 8) + head[1]
    return csum == sum(head[2:] + data)


def mkcmd(ncmd, fmt, *args):
    """Make a command packet

    Args:
        ncmd: command number
        fmt: format string, excluding header (in 'struct' notation)
        args: command arguments
    """
    fmt = '!BB' + fmt
    cmdlen = struct.calcsize(fmt) - 2
    cmd = struct.pack(fmt, ncmd, cmdlen, *args)
    packet = crc(cmd) + cmd
    return packet


def str2hex(string):
    """Hexdump a string """
    hexstr = ["%02x" % ord(c) for c in string]
    return ' '.join(hexstr)




