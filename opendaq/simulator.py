# Copyright 2012 Juan Menendez <juanmb@ingen10.com>
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

from opendaq.serial_sim import SerialSim
from opendaq.common import crc
from random import randint


NPIOS = 7
NINPUTS = 8
NGAINS = 4


class DAQSimulator(SerialSim):
    def __init__(self):
        SerialSim.__init__(self)
        self.pios = [0]*NPIOS
        self.pios_dir = [0]*NPIOS
        self.led_color = 0
        self.dac_value = 0
        self.adc_pinput = 5
        self.adc_ninput = 0
        self.adc_gain = 1
        self.adc_nsamples = 20

    @SerialSim.command(18, 'B', 'B')
    def cmd_led_w(self, color):
        """Set LED color.
        color -- LED color (0-3)

        """
        if not 0 <= color <= 3:
            raise ValueError("Invalid LED color")

        self.led_color = color
        return color

    @SerialSim.command(3, 'B', 'BB')
    def cmd_get_pio(self, npio):
        """Get the value of a PIO.
        npio -- PIO number (1-6)

        """
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")

        return npio, self.pios[npio]

    @SerialSim.command(3, 'BB', 'BB')
    def cmd_set_pio(self, npio, value):
        """Set the value of a PIO.
        npio -- PIO number (1-6)
        value -- PIO value (1, 1)

        """
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")
        if value not in (0, 1):
            raise ValueError("Invalid PIO value")

        self.pios[npio] = value
        return npio, value

    @SerialSim.command(5, 'B', 'BB')
    def cmd_get_pio_dir(self, npio):
        """Get the value of a PIO.
        npio -- PIO number (1-6)

        """
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")

        return npio, self.pios_dir[npio]

    @SerialSim.command(5, 'BB', 'BB')
    def cmd_set_pio_dir(self, npio, dir):
        """Set the value of a PIO.
        npio -- PIO number (1-6)
        dir -- PIO direction (0: input, 1: output)

        """
        if not 0 < npio <= NPIOS:
            raise ValueError("Invalid PIO number")
        if dir not in (0, 1):
            raise ValueError("Invalid PIO direction")

        self.pios_dir[npio] = dir
        return npio, dir

    @SerialSim.command(13, 'h', 'h')
    def cmd_set_daq(self, value):
        """Set DAQ output voltage.
        value -- Output voltage in mV as a signed word (16 bit) value

        """
        if not -4096 <= value < 4096:
            raise ValueError("Invalid voltage value")

        self.dac_value = value
        return value

    @SerialSim.command(1, '', 'h')
    def cmd_ain(self):
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


if __name__ == '__main__':
    import struct

    def str2hex(string):
        hexstr = ["%02x" % ord(c) for c in string]
        return ' '.join(hexstr)

    daq = DAQSimulator()

    for cmd, n in daq.list_commands():
        print "%02d: %s" % (n, cmd)

    daq.cmd_set_pio(1, 1)
    print daq.cmd_get_pio(1)

    packet = struct.pack('bb', 1, 0)
    packet = crc(packet) + packet

    daq.write(packet)
    resp = daq.read(4)
    print str2hex(resp)
