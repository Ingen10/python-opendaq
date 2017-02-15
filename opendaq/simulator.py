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

from random import randint
from .serial_sim import SerialSim

NPIOS = 7
NINPUTS = 8
NGAINS = 4
NDACS = 4


class DAQSimulator(SerialSim):
    def __init__(self, port=None, baudrate=9600, timeout=None):
        SerialSim.__init__(self, port, baudrate, timeout)
        self.pios = [0]*NPIOS
        self.pios_dir = [0]*NPIOS
        self.led_color = 0
        self.dac_values = [0]*NDACS
        self.adc_pinput = 5
        self.adc_ninput = 0
        self.adc_gain = 1
        self.adc_nsamples = 20
        self.calib_gains = [100]*17
        self.calib_offsets = [1]*17

        self.hw_ver = 0
        self.fw_ver = 56
        self.dev_id = 456423

    @SerialSim.command(18, 'B', 'B')
    def cmd_led_w(self, color):
        if not 0 <= color <= 3:
            raise ValueError("Invalid LED color")

        self.led_color = int(color)
        return color

    @SerialSim.command(3, 'B', 'BB')
    def cmd_read_pio(self, npio):
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")

        return npio, self.pios[npio-1]

    @SerialSim.command(3, 'BB', 'BB')
    def cmd_set_pio(self, npio, value):
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")
        if value not in (0, 1):
            raise ValueError("Invalid PIO value")

        self.pios[npio-1] = value
        return npio, value

    @SerialSim.command(5, 'B', 'BB')
    def cmd_get_pio_dir(self, npio):
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")

        return npio, self.pios_dir[npio-1]

    @SerialSim.command(5, 'BB', 'BB')
    def cmd_set_pio_dir(self, npio, dir):
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")
        if dir not in (0, 1):
            raise ValueError("Invalid PIO direction")

        self.pios_dir[npio-1] = dir
        return npio, dir

    @SerialSim.command(13, 'hB', 'hB')
    def cmd_set_dac(self, value, n):
        if not 0 <= n < NDACS:
            raise ValueError("Invalid DAC number")
        if not -4096 <= value < 4096:
            raise ValueError("Invalid voltage value")

        self.dac_values[n] = value
        return value, n

    @SerialSim.command(1, '', 'h')
    def cmd_read_analog(self):
        return randint(-2**14, 2**14 - 1)

    @SerialSim.command(2, 'BBBB', 'hBBBB')
    def cmd_ain_cfg(self, pinput, ninput, gain, nsamples):
        if not 0 < pinput <= NINPUTS:
            raise ValueError("Invalid positive input")
        if ninput not in (0, 5, 6, 7, 8, 25):
            raise ValueError("Invalid negative input")
        if not 0 <= gain < NGAINS:
            raise ValueError("Invalid gain")
        if not nsamples > 0:
            raise ValueError("Invalid nsamples")

        self.adc_pinput = pinput
        self.adc_ninput = ninput
        self.adc_gain = gain
        self.adc_nsamples = nsamples
        value = randint(-2**14, 2**14 - 1)
        return value, pinput, ninput, gain, nsamples

    @SerialSim.command(39, '', 'BBI')
    def cmd_idconfig(self):
        return self.hw_ver, self.fw_ver, self.dev_id

    @SerialSim.command(36, 'B', 'BHh')
    def cmd_getcalib(self, index):
        if not 0 <= index <= (5 if self.hw_ver else 16):
            raise ValueError("Invalid calibration index")
        return index, self.calib_gains[index], self.calib_offsets[index]
