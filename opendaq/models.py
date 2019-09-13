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
from .daq_model import DAQModel, INP, OUTP, PGAGains


class Gains:
    """Valid PGA gains by OpenDAQ model."""
    M = PGAGains.new([1./3, 1, 2, 10, 100])
    S = PGAGains.new([1, 2, 4, 5, 8, 10, 16, 20])
    N = PGAGains.new([1, 2, 4, 5, 8, 10, 16, 32])
    TP0X = PGAGains.new([1, 2, 4, 5, 8, 10, 16, 32])

INP_A = INP(bits=16, vmin=-24, vmax=24,
                    pga_gains=PGAGains.new([1./3, 1, 2, 10, 100]),
                    modes=[0, 1], unit='V')
INP_B = INP(bits=16, vmin=-24, vmax=24,
                    pga_gains=Gains.TP0X.values,
                    modes=[0], unit='V')
INP_M = INP(bits=16, vmin=-4.096, vmax=4.096,
                    pga_gains=Gains.M.values,
                    modes=[0, 5, 6, 7, 8, 25], unit='V')
INP_S = INP(bits=16, vmin=-12.0, vmax=12.0,
                    pga_gains=Gains.S.values,
                    modes=list(range(0, 9)), unit='V')
INP_N = INP(bits=16, vmin=-12.288, vmax=12.288,
                    pga_gains=Gains.N.values,
                    modes=list(range(0, 9)), unit='V')

OUTP_M = OUTP(bits=16, vmin=-4.096, vmax=4.096, unit='V')
OUTP_S = OUTP(bits=16, vmin=0, vmax=4.096, unit='V')
OUTP_T = OUTP(bits=16, vmin=-24, vmax=24, unit='V')
OUTP_L = OUTP(bits=16, vmin=0, vmax=40.96, unit='mA')



class ModelM(DAQModel):
    _id = 1

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='[M]', serial_fmt='ODM08%03d7',
            adc_slots=13, dac_slots=1, npios=6, nleds=1,
            dac=[OUTP_M],
            adc=8*[INP_M]
        )

    def _get_adc_slots(self, gain_id, pinput, ninput):
        """There are 13 calibration slots:
         - 8 slots, one for every pinput
         - 5 slots, one for every PGA gain.
         """
        return pinput - 1, len(self.adc) + gain_id

class ModelS(DAQModel):
    _id = 2

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='[S]', serial_fmt="ODS08%03d7",
            adc_slots=16, dac_slots=1, npios=6, nleds=1,
            dac=[OUTP_S],
            adc=8*[INP_S]
        )

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

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='[N]', serial_fmt='ODN08%03d7',
            adc_slots=16, dac_slots=1, npios=6, nleds=1,
            dac=[OUTP_M],
            adc=8*[INP_N]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        return pinput - 1, len(self.adc) + pinput - 1

class ModelTP08ABRR(DAQModel):
    _id = 10

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP08ABRR', serial_fmt='TP08x10%04d',
            adc_slots=8, dac_slots=2, npios=4, nleds=4,
            dac=2*[OUTP_T],
            adc=4*[INP_B]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1

class ModelTP08ABRR2(DAQModel): # new version of ABRR with shunt resistors for loop current
    _id = 17

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP08ABRR', serial_fmt='TP08x17%04d',
            adc_slots=8, dac_slots=2, npios=4, nleds=4,
            dac=2*[OUTP_T],
            adc=4*[INP_B]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error (depending on pinput and mode)
        - One slot to correct the gain amplification
         """
        return (pinput-1) + 2*mode, 2*len(self.adc) + (pinput-1)


class ModelTP04AR(DAQModel):
    _id = 11

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP04AR', serial_fmt='TP04x11%04d',
            adc_slots=4, dac_slots=2, npios=2, nleds=2,
            dac=2*[OUTP_T],
            adc=2*[INP_B]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP04AB(DAQModel):
    _id = 12

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP04AB', serial_fmt='TP04x12%04d',
            adc_slots=8, dac_slots=2, npios=0, nleds=4,
            dac=2*[OUTP_T],
            adc=4*[INP_B]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08RRLL(DAQModel):
    _id = 13

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP08RRLL', serial_fmt='TP08x13%04d',
            adc_slots=0, dac_slots=4, npios=4, nleds=0,
            dac=2*[OUTP_T],
            adc=4*[INP_B]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08LLLB(DAQModel):
    _id = 14

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP08LLLB', serial_fmt='TP08x14%04d',
            adc_slots=4, dac_slots=6, npios=0, nleds=2,
            dac=6*[OUTP_L],
            adc=2*[INP_B]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08LLLL(DAQModel):
    _id = 15

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP08LLLL', serial_fmt='TP08x15%04d',
            adc_slots=0, dac_slots=8, npios=0, nleds=0,
            dac=8*[OUTP_L],
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error
        - One slot to correct the gain amplification
         """
        return pinput - 1, len(self.adc) + pinput - 1


class ModelTP08LLAR(DAQModel):
    _id = 16

    def __init__(self, fw_ver, serial):
        DAQModel.__init__(
            self, fw_ver, serial,
            model_str='TP08LLAR', serial_fmt='TP08x16%04d',
            adc_slots=4, dac_slots=4, npios=2, nleds=2,
            dac=2*[OUTP_T],
            adc=2*[INP_A]
        )

    def _get_adc_slots(self, gain_id, pinput, mode):
        """There are two calibration slot for each pinput:
        - One slot to correct the analog error (depending on pinput and mode)
        - One slot to correct the gain amplification
         """
        return (pinput-1), len(self.adc) + (pinput-1)
