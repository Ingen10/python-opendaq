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
from .daq_model import DAQModel, InputBase, OutputBase, PGAGains
from enum import Enum


class InputType(Enum):
    INPUT_TYPE_A = 1
    INPUT_TYPE_AS = 2
    INPUT_TYPE_M = 3
    INPUT_TYPE_S = 4
    INPUT_TYPE_N = 5

class OutputType(Enum):
    OUTPUT_TYPE_M = 1
    OUTPUT_TYPE_S = 2
    OUTPUT_TYPE_T = 3
    OUTPUT_TYPE_L = 4

class InputA(InputBase):
    # Analog input without shut
    _input_id = InputType.INPUT_TYPE_A
    def __init__(self, calib=None):
        InputBase.__init__(self)
 
class InputAS(InputBase):
    # Analog input with shunt
    _input_id = InputType.INPUT_TYPE_AS
    def __init__(self, calib=None):
        InputBase.__init__(self, 
            type_str = 'INPUT_TYPE_AS',
            inputmodes = [0, 1]
        )
    def raw_to_units(self, raw, gain_id, calibreg1, calibreg2, inputmode):
        adc_gain = 2.**(self.bits-1)/self.vmax
        if inputmode:
            gain = adc_gain*self._gains[gain_id]*calibreg1.gain
            offset = calibreg1.offset*self._gains[gain_id]
            fact = 10.0
        else:
            gain = adc_gain*self._gains[gain_id]*calibreg1.gain*calibreg2.gain
            offset = calibreg1.offset + calibreg2.offset*self._gains[gain_id]
            fact = 1.0
        print(gain)
        print(offset)
        print(fact)
        try:
            result = [round((v - offset)*fact/gain, 5) for v in raw]
        except TypeError:
            result = round((raw - offset)*fact/gain, 5)
        return (result, self.unit)

class InputM(InputBase):
    # Analog input with shunt
    _input_id = InputType.INPUT_TYPE_M
    def __init__(self, calib=None):
        InputBase.__init__(self, 
            type_str = 'INPUT_TYPE_M',
            inputmodes = [0, 5, 6, 7, 8, 25],
            _gains = [1./3, 1, 2, 10, 100],
            vmin = -4.096,
            vmax = 4.096
        )

class InputS(InputBase):
    # Analog input with shunt
    _input_id = InputType.INPUT_TYPE_S
    def __init__(self, calib=None):
        InputBase.__init__(self,
            type_str = 'INPUT_TYPE_S',
            inputmodes = list(range(0, 9)),
            _gains = [1, 2, 4, 5, 8, 10, 16, 20],
            vmin = -12.0,
            vmax = 12.0
        )

class InputN(InputBase):
    # Analog input with shunt
    _input_id = InputType.INPUT_TYPE_N
    def __init__(self, calib=None):
        InputBase.__init__(self, 
            type_str = 'INPUT_TYPE_N',
            inputmodes = list(range(0, 9)),
            vmin = -12.288,
            vmax = 12.288
        )

class OutputS(OutputBase):
    # Opendaq S output
    _output_id = OutputType.OUTPUT_TYPE_S
    def __init__(self):
        OutputBase.__init__(self, 
            type_str = 'OUTPUT_TYPE_S',
            vmin = 0,
            vmax = 4.096
        )

class OutputL(OutputBase):
    # Current output
    _output_id = OutputType.OUTPUT_TYPE_L
    def __init__(self):
        OutputBase.__init__(self,
            type_str = 'OUTPUT_TYPE_L',
            vmin = 0,
            vmax = 40.96,
            unit = 'mA'
        )

class OutputM(OutputBase):
    # Tachometer output
    _output_id = OutputType.OUTPUT_TYPE_M
    def __init__(self):
        OutputBase.__init__(self, 
            type_str = 'OUTPUT_TYPE_M',
            vmin = -4.096,
            vmax = 4.096
        )

class OutputT(OutputBase):
    # Tachometer output
    _output_id = OutputType.OUTPUT_TYPE_T
    def __init__(self):
        OutputBase.__init__(self, 
            type_str = 'OUTPUT_TYPE_T',
        )

class ModelM(DAQModel):
    _id = 1
    model_str='[M]'
    serial_fmt='ODM08%03d7'
    adc_slots=13
    dac_slots=1
    npios=6
    nleds=1
    _output_t=[OutputType.OUTPUT_TYPE_M]
    _input_t=8*[InputType.INPUT_TYPE_M]

    def _get_adc_slots(self, gain_id, pinput, ninput):
        """There are 13 calibration slots:
         - 8 slots, one for every pinput
         - 5 slots, one for every PGA gain.
         """
        return pinput - 1, len(self.adc) + gain_id

class ModelS(DAQModel):
    _id = 2
    model_str='[S]'
    serial_fmt='ODS08%03d7'
    adc_slots=16
    dac_slots=1
    npios=6
    nleds=1
    _output_t=[OutputType.OUTPUT_TYPE_S]
    _input_t=8*[InputType.INPUT_TYPE_S]

    def check_adc_settings(self, pinput, mode, gain):
        DAQModel.check_adc_settings(self, pinput, mode, gain)

        if gain > 0 and mode == 0:
            raise ValueError("Invalid gain selection")
        if mode != 0 and (pinput % 2 == 0 and mode != pinput - 1 or
                            pinput % 2 != 0 and mode != pinput + 1):
            raise ValueError("Invalid negative input selection")

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are 16 calibration slots:
          - Single-ended mode: use the first 8 slots
          - Differential mode: use the last 8 slots
         """
        offs = 0 if mode == 0 else 8
        return pinput - 1 + offs, -1


class ModelN(DAQModel):
    _id = 3
    model_str='[N]'
    serial_fmt='ODN08%03d7'
    adc_slots=16
    dac_slots=1
    npios=6
    nleds=1
    _output_t=[OutputType.OUTPUT_TYPE_M]
    _input_t=8*[InputType.INPUT_TYPE_N]

    def _get_adc_slots(self, gain_id, pinput, mode):
        return pinput - 1, len(self.adc) + pinput - 1

class ModelTP08ABRR(DAQModel):
    _id = 10
    model_str='TP08ABRR'
    serial_fmt='TP08x10%04d'
    adc_slots=8
    dac_slots=2
    npios=4
    nleds=4
    _output_t=2*[OutputType.OUTPUT_TYPE_T]
    _input_t=4*[InputType.INPUT_TYPE_A]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1

class ModelTP08ABRR2(DAQModel): # new version of ABRR with shunt resistors for loop current
    _id = 17
    model_str='TP08ABRR'
    serial_fmt='TP08x10%04d'
    adc_slots=12
    dac_slots=2
    npios=4
    nleds=4
    _output_t=2*[OutputType.OUTPUT_TYPE_T]
    _input_t=4*[InputType.INPUT_TYPE_AS]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error (depending on pinput and mode)
        - One slot to correct the gain amplification
         """
        idx = 2 * len(self.adc) * mode + pinput - 1
        return idx, len(self.adc) + pinput - 1


class ModelTP04AR(DAQModel):
    _id = 11
    model_str='TP04AR'
    serial_fmt='TP04x10%04d'
    adc_slots=4
    dac_slots=2
    npios=2
    nleds=2
    _output_t=2*[OutputType.OUTPUT_TYPE_T]
    _input_t=2*[InputType.INPUT_TYPE_A]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP04AB(DAQModel):
    _id = 12
    model_str='TP04AB'
    serial_fmt='TP04x10%04d'
    adc_slots=8
    dac_slots=2
    npios=0
    nleds=4
    _output_t=2*[OutputType.OUTPUT_TYPE_T]
    _input_t=4*[InputType.INPUT_TYPE_A]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08RRLL(DAQModel):
    _id = 13
    model_str='TP08RRLL'
    serial_fmt='TP08x10%04d'
    adc_slots=0
    dac_slots=4
    npios=4
    nleds=0
    _output_t=4*[OutputType.OUTPUT_TYPE_L]
    _input_t=[]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08LLLB(DAQModel):
    _id = 14
    model_str='TP08LLLB'
    serial_fmt='TP08x10%04d'
    adc_slots=4
    dac_slots=6
    npios=0
    nleds=2
    _output_t=6*[OutputType.OUTPUT_TYPE_L]
    _input_t=2*[InputType.INPUT_TYPE_A]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08LLLL(DAQModel):
    _id = 15
    model_str='TP08LLLL'
    serial_fmt='TP08x10%04d'
    adc_slots=0
    dac_slots=8
    npios=0
    nleds=0
    _output_t=8*[OutputType.OUTPUT_TYPE_L]
    _input_t=[]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08LLAR(DAQModel):
    _id = 16
    model_str='TP08LLAR'
    serial_fmt='TP08x10%04d'
    adc_slots=6
    dac_slots=4
    npios=2
    nleds=2
    _output_t=4*[OutputType.OUTPUT_TYPE_L]
    _input_t=2*[InputType.INPUT_TYPE_AS]

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error (depending on pinput and mode)
        - One slot to correct the gain amplification
         """
        idx = 2 * len(self.adc) * mode + pinput - 1
        return idx, len(self.adc) + pinput - 1
