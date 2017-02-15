#!/usr/bin/env python

# Copyright 2016
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
from functools import wraps
from .common import check_crc, LengthError, mkcmd


class SerialSim(object):
    __commands = {}

    def __init__(self, port=None, baudrate=9600, timeout=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._init()

    def _init(self):
        self.rts = 1
        self.port_open = True
        self.NACK = '\x00\xa0\xa0\x00'
        self.__out_buf = bytearray()

    @classmethod
    def command(cls, ncmd, cmd_fmt, ret_fmt):
        """Command decorator"""
        def inner_command(f):
            cmd_len = struct.calcsize(cmd_fmt)
            cls.__commands[f.__name__] = (f, ncmd, cmd_len, cmd_fmt, ret_fmt)

            def wrapped(*args, **kwargs):
                return f(*args, **kwargs)

            return wraps(f)(wrapped)
        return inner_command

    def __get_command(self, ncmd, length):
        try:
            ret = next((e for e in self.__commands.values()
                        if e[1] == ncmd and e[2] == length))
        except StopIteration:
            raise ValueError("Invalid command number")
        return ret

    def __unpack_header(self, data):
        pay_len = len(data) - 4
        ncmd, length, cmd_data = struct.unpack('!bb%ds' % pay_len,
                                               check_crc(data))
        if pay_len != length:
            raise LengthError("Wrong command length")
        return ncmd, length, cmd_data

    def __pack_response(self, ncmd, ret_values, fmt=''):
        if not type(ret_values) is tuple:
            ret_values = (ret_values,)
        return mkcmd(ncmd, fmt, *ret_values)

    def list_commands(self):
        cmd_list = [(cmd, lst[1]) for cmd, lst in
                    list(self.__commands.items())]
        return sorted(cmd_list, key=lambda cmd: cmd[1])

    def exec_command(self, data):
        try:
            ncmd, ln, cmd_data = self.__unpack_header(data)
            f, _, _, cmd_fmt, ret_fmt = self.__get_command(ncmd, ln)
            args = struct.unpack('!'+cmd_fmt, cmd_data)
            ret = self.__pack_response(ncmd, f(self, *args), ret_fmt)
        except (LengthError, ValueError):
            return self.NACK
        return ret

    def write(self, data):
        if not self.port_open:
            raise IOError("Port is closed")

        self.__out_buf.extend(self.exec_command(data))
        return len(data)

    def read(self, size=1):
        if not self.port_open:
            raise IOError("Port is closed")

        ret = bytearray()
        for i in range(size):
            try:
                ret.append(self.__out_buf.pop(0))
            except IndexError:
                break
        return str(ret)

    def flushInput(self):
        self.__out_buf = bytearray()

    def open(self):
        self.port_open = True

    def close(self):
        self._init()
        self.port_open = False

    def setRTS(self, value):
        self.rts = value
