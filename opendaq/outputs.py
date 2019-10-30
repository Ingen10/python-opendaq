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

from __future__ import division

from enum import Enum


class OutputBase(object):
    _output_id = 0

    def __init__(self, type_str='OUTP_T', bits=16, vmin=-24, vmax=24, unit='V'):
        self.type_str = type_str
        self.bits = bits
        self.vmin = vmin
        self.vmax = vmax
        self.unit = unit

    @classmethod
    def new(cls, output_id):
        """Factory method for instantiating subclasses of OutputBase."""
        for model in cls.__subclasses__():
            if model._output_id == output_id:
                return model()
        raise ValueError("Unknown output ID")


class OutputType(Enum):
    OUTPUT_TYPE_M = 1
    OUTPUT_TYPE_S = 2
    OUTPUT_TYPE_T = 3
    OUTPUT_TYPE_L = 4


class OutputS(OutputBase):
    # Opendaq S output
    _output_id = OutputType.OUTPUT_TYPE_S

    def __init__(self):
        OutputBase.__init__(self,
                            type_str='OUTPUT_TYPE_S',
                            vmin=0,
                            vmax=4.096
                            )


class OutputL(OutputBase):
    # Current output
    _output_id = OutputType.OUTPUT_TYPE_L

    def __init__(self):
        OutputBase.__init__(self,
                            type_str='OUTPUT_TYPE_L',
                            vmin=0,
                            vmax=40.96,
                            unit='mA'
                            )


class OutputM(OutputBase):
    # openDAQ M/N output
    _output_id = OutputType.OUTPUT_TYPE_M

    def __init__(self):
        OutputBase.__init__(self,
                            type_str='OUTPUT_TYPE_M',
                            vmin=-4.096,
                            vmax=4.096
                            )


class OutputT(OutputBase):
    # Tachometer output
    _output_id = OutputType.OUTPUT_TYPE_T

    def __init__(self):
        OutputBase.__init__(self,
                            type_str='OUTPUT_TYPE_T',
                            )
