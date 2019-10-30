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
import numpy as np

from .daq_model import PGAGains


class InputBase(object):
    _input_id = 0

    def __init__(self, calib=None, type_str='INP_A', bits=16, vmin=-24, vmax=24,
                 _gains=[1, 2, 4, 5, 8, 10, 16, 32], inputmodes=[0], unit=["V"]):
        self.type_str = type_str
        self.bits = bits
        self.vmin = vmin
        self.vmax = vmax
        self._gains = _gains
        self.inputmodes = inputmodes
        self.unit = unit

        self.pga_gains = PGAGains.new(self._gains)
        self.calib = calib

    def raw_to_units(self, raw, gain_id, calibreg1, calibreg2, inputmode=0):
        adc_gain = 2.**(self.bits-1)/self.vmax
        gain = adc_gain*self._gains[gain_id]*calibreg1.gain*calibreg2.gain
        offset = calibreg1.offset + calibreg2.offset*self._gains[gain_id]
        try:
            result = [round((v - offset)/gain, 5) for v in raw]
        except TypeError:
            result = round((raw - offset)/gain, 5)
        return (result, self.unit[inputmode])

    @classmethod
    def new(cls, input_id, calib=None):
        """Factory method for instantiating subclasses of InputBase."""
        for model in cls.__subclasses__():
            if model._input_id == input_id:
                return model(calib)
        raise ValueError("Unknown input ID")


class InputType(Enum):
    INPUT_TYPE_A = 1
    INPUT_TYPE_AS = 2
    INPUT_TYPE_M = 3
    INPUT_TYPE_S = 4
    INPUT_TYPE_N = 5
    INPUT_TYPE_P = 6


class InputA(InputBase):
    # Analog input without shut
    _input_id = InputType.INPUT_TYPE_A

    def __init__(self, calib=None):
        InputBase.__init__(self)


class InputP(InputBase):
    # Analog input without shut
    _input_id = InputType.INPUT_TYPE_P

    def __init__(self, calib=None):
        InputBase.__init__(self,
                           type_str='INPUT_TYPE_P',
                           inputmodes=[0, 1],
                           unit=["Ohm", "ºC"],
                           _gains=[1]
                           )

    def raw_to_units(self, raw, gain_id, calibreg1, calibreg2, inputmode=0):
        T_MAX = 70
        T_MIN = -20
        adc_gain = 2.**(self.bits-1)/self.vmax
        gain = adc_gain*self._gains[gain_id]*calibreg1.gain*calibreg2.gain
        offset = calibreg1.offset + calibreg2.offset*self._gains[gain_id]
        try:
            result = [10.0 * round((v - offset)/gain, 5) + 250.0 for v in raw]
        except TypeError:
            result = 10.0 * round((raw - offset)/gain, 5) + 250.0
        if inputmode:
            res = result
            coefs = [4.183 * 10 ** (-10), 4.183 * 10 ** (-8), 5.775 * 10 ** (-5),
                     -0.39083, (res - 100)]
            results = abs(np.roots(coefs))
            for r in results:
                if r.imag == 0 and r < T_MAX and r > T_MIN:
                    result = r.real
                    if res < 100.0:
                        result *= -1
        return (result, self.unit[inputmode])


class InputAS(InputBase):
    # Analog input with shunt
    _input_id = InputType.INPUT_TYPE_AS

    def __init__(self, calib=None):
        InputBase.__init__(self,
                           type_str='INPUT_TYPE_AS',
                           inputmodes=[0, 1],
                           unit=['V', 'mA']
                           )

    def raw_to_units(self, raw, gain_id, calibreg1, calibreg2, inputmode=0):
        adc_gain = 2.**(self.bits-1)/self.vmax
        gain = adc_gain*self._gains[gain_id]*calibreg1.gain*calibreg2.gain
        offset = calibreg1.offset + calibreg2.offset*self._gains[gain_id]
        try:
            result = [round((v - offset)/gain, 5) for v in raw]
        except TypeError:
            result = round((raw - offset)/gain, 5)
        if inputmode:
            try:
                result = [(10.0 * r) for r in result]
            except TypeError:
                result *= 10.0
        return (result, self.unit[inputmode])


class InputM(InputBase):
    # openDAQ M analog input
    _input_id = InputType.INPUT_TYPE_M

    def __init__(self, calib=None):
        InputBase.__init__(self,
                           type_str='INPUT_TYPE_M',
                           inputmodes=[0, 5, 6, 7, 8, 25],
                           _gains=[1./3, 1, 2, 10, 100],
                           vmin=-4.096,
                           vmax=4.096
                           )


class InputS(InputBase):
    # openDAQ S analog input
    _input_id = InputType.INPUT_TYPE_S

    def __init__(self, calib=None):
        InputBase.__init__(self,
                           type_str='INPUT_TYPE_S',
                           inputmodes=list(range(0, 9)),
                           _gains=[1, 2, 4, 5, 8, 10, 16, 20],
                           vmin=-12.0,
                           vmax=12.0
                           )


class InputN(InputBase):
    # openDAQ N analog input
    _input_id = InputType.INPUT_TYPE_N

    def __init__(self, calib=None):
        InputBase.__init__(self,
                           type_str='INPUT_TYPE_N',
                           inputmodes=list(range(0, 9)),
                           vmin=-12.288,
                           vmax=12.288
                           )
