#!/usr/bin/env python

# Copyright 2013
# Adrian Alvarez <alvarez@ingen10.com>, Juan Menendez <juanmb@ingen10.com>
# and Armando Vincelle <armando@ingen10.com>
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
import time
import serial
from opendaq.common import crc, check_crc, mkcmd, CRCError, LengthError
from opendaq.simulator import DAQSimulator

BAUDS = 115200
INPUT_MODES = ('ANALOG_INPUT', 'ANALOG_OUTPUT', 'DIGITAL_INPUT',
               'DIGITAL_OUTPUT', 'COUNTER_INPUT', 'CAPTURE_INPUT')
LED_OFF = 0
LED_GREEN = 1
LED_RED = 2

NAK = mkcmd(160, '')


class DAQ:
    def __init__(self, port, debug=False):
        """Class constructor"""
        self.port = port
        self.debug = debug
        self.simulate = (port == 'sim')

        self.measuring = False
        self.gain = 0
        self.pinput = 1
        self.open()

        info = self.get_info()
        self.hw_ver = 'm' if info[0] == 1 else 's'
        self.gains, self.offsets = self.get_cal()
        self.dac_gain, self.dac_offset = self.get_dac_cal()

    def open(self):
        """Open the serial port"""
        if self.simulate:
            self.ser = DAQSimulator(self.port, BAUDS, timeout=1)
        else: 
            self.ser = serial.Serial(self.port, BAUDS, timeout=1)
            self.ser.setRTS(0)
            time.sleep(2)

    def close(self):
        """Close the serial port"""
        self.ser.close()

    def send_command(self, cmd, ret_fmt):
        """Build a command packet, send it to the openDAQ and process the
        response

        Args:
            cmd: Command ID
            ret_fmt: Payload format using python 'struct' format characters
        Returns:
            Command ID and arguments of the response
        Raises:
            LengthError: The legth of the response is not the expected
        """
        if self.measuring:
            self.stop()

        # Add 'command' and 'length' fields to the format string
        fmt = '!BB' + ret_fmt
        ret_len = 2 + struct.calcsize(fmt)
        packet = crc(cmd) + cmd
        self.ser.write(packet)
        ret = self.ser.read(ret_len)
        if self.debug:
            print 'Command:  ',
            for c in packet:
                print '%02X' % ord(c),
            print
            print 'Response: ',
            for c in ret:
                print '%02X' % ord(c),
            print

        if ret == NAK:
            raise IOError("NAK response received")

        data = struct.unpack(fmt, check_crc(ret))

        if len(ret) != ret_len:
            raise LengthError("Bad packet length %d (it should be %d)" %
                              (len(ret), ret_len))
        if data[1] != ret_len-4:
            raise LengthError("Bad body length %d (it should be %d)" %
                              (ret_len-4, data[1]))
        # Strip 'command' and 'length' values from returned data
        return data[2:]

    def get_info(self):
        """Read device configuration

        Returns:
            [hardware version, firmware version, device ID number]
        """
        return self.send_command('\x27\x00', 'BBI')

    def read_adc(self):
        """Read data from ADC and return the raw value

        Returns:
            Raw ADC value
        """
        value = self.send_command('\x01\x00', 'h')[0]
        return value

    def read_analog(self):
        """Read data from ADC in volts

        Returns:
            Voltage value
        """
        value = self.send_command('\x01\x00', 'h')[0]
        # Raw value to voltage->
        index = self.gain + 1 if self.hw_ver == 'm' else self.pinput
        value *= self.gains[index]
        value = -value/1e5 if self.hw_ver == 'm' else value/1e4
        value = (value + self.offsets[index])/1e3
        return value

    def conf_adc(self, pinput, ninput=0, gain=0, nsamples=20):
        """ Configure the ADC

        Args:
            pinput: Positive input (1-8)
            ninput: Negative input (0, 5, 6, 7, 8, 25)
            gain: Analog gain (0:x1/3, 1:x1, 2:x2, 3:x10, 4:x100)
            nsamples: Number of samples per point (1-255)
        """
        self.gain = gain

        if self.hw_ver == 's' and ninput != 0:
            self.pinput = (pinput - 1)/2 + 9
        else:
            self.pinput = pinput

        cmd = struct.pack('!BBBBBB', 2, 4, pinput, ninput, gain, nsamples)
        self.send_command(cmd, 'hBBBB')

    def enable_crc(self, on):
        """Enable/Disable the cyclic redundancy check

        Args:
            on: Enable CRC
        """
        cmd = struct.pack('!BBB', 55, 1, on)
        self.send_command(cmd, 'B')[0]

    def set_led(self, color):
        """Set LED color

        Args:
            color: LED color (0:off, 1:green, 2:red, 3:orange)
        Raises:
            ValueError: Invalid color number
        """
        if not 0 <= color <= 3:
            raise ValueError('Invalid color number')
        cmd = struct.pack('!BBB', 18, 1, color)
        self.send_command(cmd, 'B')[0]

    def set_analog(self, volts):
        """Set DAC output voltage. Device calibration values are taken into
        account

        openDAQ[M] range: -4.096 V to +4.096 V

        openDAQ[S] range: 0 V to +4.096 V

        Args:
            volts: New DAC output value in volts
        Raises:
            ValueError: DAC voltage out of range

        """
        value = int(round(volts*1000))

        if self.hw_ver == 'm' and not -4096 <= value < 4096:
            raise ValueError('DAC voltage out of range')
        elif self.hw_ver == 's' and not 0 <= value < 4096:
            raise ValueError('DAC voltage out of range')

        data = 2*(value * self.dac_gain/1000.0 + self.dac_offset + 4096)
        if self.hw_ver == 's':
            data = max(0, min(data, 32767))  # clamp value

        cmd = struct.pack('!BBh', 24, 2, data)
        self.send_command(cmd, 'h')[0]

    def set_dac(self, raw):
        """Set DAC output (binary value)

        Args:
            raw: Raw binary value
        Raises:
            ValueError: DAC voltage out of range
        """
        value = int(round(raw))
        if not 0 < value < 16384:
            raise ValueError('DAC value out of range')

        cmd = struct.pack('!BBH', 24, 2, value)
        self.send_command(cmd, 'h')[0]

    def set_port_dir(self, output):
        """Configure all PIO directions

        Args:
            output: Port direction byte (bits: 0:input, 1:output)
        """
        cmd = struct.pack('!BBB', 9, 1, output)
        self.send_command(cmd, 'B')[0]

    def set_port(self, value):
        """Write all PIO values

        Args:
            value: Port output byte (bits: 0:low, 1:high)
        """
        cmd = struct.pack('!BBB', 7, 1, value)
        self.send_command(cmd, 'B')[0]

    def set_pio_dir(self, number, output):
        """Configure PIO direction

        Args:
            number: DIO number (1-6)
            output: DIO direction (0 input, 1 output)
        Raises:
            ValueError: Invalid DIO number
        """
        if not 1 <= number <= 6:
            raise ValueError('Invalid DIO number')

        cmd = struct.pack('!BBBB', 5, 2, number,  int(bool(output)))
        self.send_command(cmd, 'BB')

    def set_pio(self, number, value):
        """Write DIO output

        Args:
            number: DIO number (1-6)
            value: digital value
        Raises:
            ValueError: Invalid DIO number
        """
        if not 1 <= number <= 6:
            raise ValueError('Invalid PIO number')

        cmd = struct.pack('!BBBB', 3, 2, number, int(bool(value)))
        self.send_command(cmd, 'BB')

    def init_counter(self, edge):
        """Initialize the edge counter

        Args:
            edge: high-to-low (0) or low-to-high (1)
        """
        cmd = struct.pack('!BBB', 41, 1, 1)
        self.send_command(cmd, 'B')[0]

    def get_counter(self, reset):
        """Get the counter value

        Args:
            reset: reset the counter after reading
        """
        cmd = struct.pack('!BBB', 42, 1, reset)
        return self.send_command(cmd, 'H')[0]

    def init_capture(self, period):
        """Start capture mode around a given period

        Args:
            period: period of the wave (microseconds)
        """
        cmd = struct.pack('!BBH', 14, 2, period)
        return self.send_command(cmd, 'H')[0]

    def stop_capture(self):
        """Stop capture mode
        """
        self.send_command('\x0F\x00', '')

    def get_capture(self, mode):
        """Get current period length

        Args:
            mode: Period length (0: Low cycle, 1: High cycle, 2: Full period)
        Returns:
            Period length in microseconds
        """
        cmd = struct.pack('!BBB', 16, 1, mode)
        return self.send_command(cmd, 'BH')

    def init_encoder(self, resolution):
        """Start encoder function

        Args:
            resolution: Maximum number of ticks per round [0:65535]
        """
        cmd = struct.pack('!BBB', 50, 1, resolution)
        return self.send_command(cmd, 'B')[0]

    def get_encoder(self):
        """Get current encoder relative position

        Returns:
            Current encoder value
        """
        return self.send_command('\x34\x00', 'H')

    def init_pwm(self, duty, period):
        """Start PWM output with a given period and duty cycle

        Args:
            duty: High time of the signal [0:1023]
            period: Frecuency of the signal in microseconds [0:65535]
        """
        cmd = struct.pack('!BBHH', 10, 4, duty, period)
        return self.send_command(cmd, 'HH')

    def stop_pwm(self):
        """Stop PWM"""
        self.send_command('\x0b\x00', '')

    def __get_calibration(self, gain_id):
        """
        Read device calibration for a given analog configuration

        Gets calibration gain and offset for the corresponding analog
        configuration

        Args:
            gain_id: analog configuration
            (1-6 for openDAQ [M])
            (1-17 for openDAQ [S])
        Returns:
            Gain (*100000[M] or *10000[S])
            Offset
        """
        cmd = struct.pack('!BBB', 36, 1, gain_id)
        return self.send_command(cmd, 'BHh')

    def get_cal(self):
        """
        Read device calibration

        Gets calibration values for all the available device configurations

        Returns:
            Gains
            Offsets
        """
        gains = []
        offsets = []
        _range = 6 if self.hw_ver == "m" else 17
        for i in range(_range):
            gain_id, gain, offset = self.__get_calibration(i)
            gains.append(gain)
            offsets.append(offset)
        return gains, offsets

    def get_dac_cal(self):
        """
        Read DAC calibration

        Returns:
            DAC gain
            DAC offset
        """
        gain_id, gain, offset = self.__get_calibration(0)
        return gain, offset

    def __set_calibration(self, gain_id, gain, offset):
        """
        Set device calibration

        Args:
            gain_id: ID of the analog configuration setup
            gain: Gain multiplied by 100000 ([M]) or 10000 ([S])
            offset: Offset raw value (-32768 to 32768)
        """
        cmd = struct.pack('!BBBHh', 37, 5, gain_id, gain, offset)
        return self.send_command(cmd, 'BHh')

    def set_cal(self, gains, offsets, flag):
        """
        Set device calibration

        Args:
            gains: Gain multiplied by 100000 ([M]) or 10000 ([S])
            offsets: Offset raw value (-32768 to 32768)
            flag: 'M', 'SE' or 'DE'
        """
        if flag == 'M':
            for i in range(1, 6):
                self.__set_calibration(i, gains[i-1], offsets[i-1])
        elif flag == 'SE':
            for i in range(1, 9):
                self.__set_calibration(i, gains[i-1], offsets[i-1])
        elif flag == 'DE':
            for i in range(9, 17):
                self.__set_calibration(i, gains[i-9], offsets[i-9])
        else:
            raise ValueError("Invalid flag")

    def set_DAC_cal(self, gain, offset):
        """
        Set DAC calibration
        """
        self.__set_calibration(0, gain, offset)

    def conf_channel(
            self, number, mode, pinput=1, ninput=0, gain=1, nsamples=1):
        """
        Configure a stream experiment (ANALOG, +IN, -IN, GAIN)

        Args:
            number: variable that defines the number of DataChannel
            to assign. (1-4)
            mode: variable that defines mode [0:5], 0 ANALOG_INPUT,
            1 ANALOG_OUTPUT, 2 DIGITAL_INPUT, 3 DIGITAL_OUTPUT,
            4 COUNTER_INPUT, 5 CAPTURE INPUT
            pinput: variable that defines positive/SE analog input [1:8]
            (default 5)
            ninput: variable that defines negative analog input
            [0 (GND), 25 (2.5V Vref), 5:8] (default 0)
            gain: variable that defines gain multiplier [0:4]
            (0 x(1/2), 1 x(1), 2 x(2, 3 x(10), 4 x(100) default(1))
            nsamples: variable that defines number of samples per point
            [1:255]
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')
        if type(mode) == str and mode in INPUT_MODES:
            mode = INPUT_MODES.index(mode)
        cmd = struct.pack('!BBBBBBBB', 22, 6, number, mode,
                          pinput, ninput, gain, nsamples)
        return self.send_command(cmd, '!BBBBBB')

    def setup_channel(self, number, npoints, continuous=True):
        """
        Configure the experiment's number of points

        Args:
            number: variable that defines the number of DataChannel
            to assign
            npoints: variable that defines the number of total points
            [0:65536] (0 indicates continuous acquisition)
            continuous: variable that defines repetition mode [0:1]
            0 continuous, 1 run once
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')
        cmd = struct.pack('!BBBHb', 32, 4, number, npoints, int(continuous))
        return self.send_command(cmd, 'BHB')

    def destroy_channel(self, number):
        """
        Delete Datachannel structure

        Args:
            number: variable that defines the number of DataChannel to clear
            [0:4] 0 reset all DataChannel
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')
        cmd = struct.pack('>BBB', 57, 1, number)
        return self.send_command(cmd, 'B')

    def create_stream(self, number, period):
        """
        Create stream experiment

        Args:
            number: variable that defines the number of DataChannel to assign
            [1:4]
            period: variable that defines the period of the stream experiment
            [1:65536]
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')
        if not 1 <= period <= 65535:
            raise ValueError('Invalid period')
        cmd = struct.pack('>BBBH', 19, 3, number, period)
        return self.send_command(cmd, 'BH')

    def create_burst(self, period):
        """
        Create burst experiment

        Args:
            period: variable that defines the period of the burst experiment
            (microseconds) [100:65535]
        """
        cmd = struct.pack('>BBH', 21, 2, period)
        return self.send_command(cmd, 'H')

    def create_external(self, number, edge):
        """
        Create external experiment

        Args:
            number: variable that defines the number of DataChannel to assign
            [1:4]
            edge: [0:1]
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')
        cmd = struct.pack('>BBBB', 20, 2, number, edge)
        return self.send_command(cmd, 'BB')

    def load_signal(self, data, offset):
        """
        Load an array of values to preload DAC output

        Args:
            data: variable that defines the data number [1:400]
            offset: variable that defines the offset
        """
        cmd = struct.pack(
            '>bBh%dH' % len(data), 23, len(data) * 2 + 2, offset, *data)
        return self.send_command(cmd, 'Bh')

    def start(self):
        """
        Start an automated measurement
        """
        self.send_command('\x40\x00', '')
        self.measuring = True

    def stop(self):
        """
        Stop actual measurement
        """

        self.measuring = False
        while True:
            try:
                self.send_command('\x50\x00', '')
                break
            except:
                time.sleep(0.2)
                self.flush()

    def flush(self):
        """
        Call ser.flushInput()
        """
        self.ser.flushInput()

    def flush_stream(self, data, channel):
        """
        Flush stream data from buffer

        Args:
           data: variable that defines the data
           channel: variable that defines the channel
        Raises:
           LengthError: An error ocurred
        """
        # Receive all stream data in the in buffer
        while 1:
            ret = self.ser.read(1)
            if not ret:
                break
            else:
                cmd = struct.unpack('>b', ret)
                if cmd[0] == 0x7E:
                    self.header = []
                    self.data = []
                    while len(self.header) < 8:
                        ret = self.ser.read(1)
                        char = struct.unpack('>B', ret)
                        if char[0] == 0x7D:
                            ret = self.ser.read(1)
                        self.header.append(char[0])
                    length = self.header[3]
                    self.dataLength = length - 4
                    while len(self.data) < self.dataLength:
                        ret = self.ser.read(1)
                        char = struct.unpack('>B', ret)
                        if char[0] == 0x7D:
                            ret = self.ser.read(1)
                            char = struct.unpack('>B', ret)
                            tmp = char[0] | 0x20
                            self.data.append(tmp)
                        else:
                            self.data.append(char[0])
                    if check_stream_crc(self.header, self.data) != 1:
                        continue
                    for i in range(0, self.dataLength, 2):
                        value = (self.data[i] << 8) | self.data[i+1]
                        if value >= 32768:
                            value -= 65536
                        data.append(int(value))
                        channel.append(self.header[4]-1)
                else:
                    break
        ret = self.ser.read(3)
        ret += str(cmd[0])
        if len(ret) != 4:
            raise LengthError

    # This function reads a stream from serial connection
    # Returns 0 if there is not incoming data
    # Returns 1 if data stream was precessed
    # Returns 2 if no data stream was received (useful for debugging)
    def get_stream(self, data, channel, callback=0):
        """Get stream from serial connection

        Args:
            data: variable that defines the data
            channel: variable that defines the channel
            callback: variable that defines the callback mode

        Returns:
            0 if there is not any incoming data.
            1 if data stream was processed.
            2 if no data stream received.
        """
        self.header = []
        self.data = []
        ret = self.ser.read(1)
        if not ret:
            return 0
        head = struct.unpack('>b', ret)
        if head[0] != 0x7E:
            data.append(head[0])
            return 2
        # Get header
        while len(self.header) < 8:
            ret = self.ser.read(1)
            char = struct.unpack('>B', ret)
            if char[0] == 0x7D:
                ret = self.ser.read(1)
                char = struct.unpack('>B', ret)
                tmp = char[0] | 0x20
                self.header.append(tmp)
            else:
                self.header.append(char[0])
            if len(self.header) == 3 and self.header[2] == 80:
                # openDAQ sent a stop command
                ret = self.ser.read(2)
                char, ch = struct.unpack('>BB', ret)
                channel.append(ch-1)
                return 3
        self.dataLength = self.header[3] - 4
        while len(self.data) < self.dataLength:
            ret = self.ser.read(1)
            char = struct.unpack('>B', ret)
            if char[0] == 0x7D:
                ret = self.ser.read(1)
                char = struct.unpack('>B', ret)
                tmp = char[0] | 0x20
                self.data.append(tmp)
            else:
                self.data.append(char[0])
        for i in range(0, self.dataLength, 2):
            value = (self.data[i] << 8) | self.data[i+1]
            if value >= 32768:
                value -= 65536
            data.append(int(value))
        check_stream_crc(self.header, self.data)
        channel.append(self.header[4]-1)
        return 1

    def set_DAC_gain_offset(self, gain, offset):
        """
        Set DAC gain and offset

        Args:
            gain: DAC gain
            offset: DAC offset
        """
        self.dac_gain = gain
        self.dac_offset = offset

    def set_gains_offsets(self, gains, offsets):
        """
        Set gains and offsets

        Args:
            gains: Gains
            offsets: Offsets
        """
        self.gains = gains
        self.offsets = offsets

    def set_id(self, id):
        """
        Identify openDAQ device

        Args:
            id: variable that defines id number [000:999]
        """
        cmd = struct.pack('>BBI', 39, 4, id)
        return self.send_command(cmd, 'bbI')

    def spi_config(self, cpol, cpha):
        """Configure bit-bang SPI (clock properties)

        Args:
            cpol: Clock polarity (clock pin state when inactive)
            cpha: Clock phase (leading 0, or trailing 1 edges read)
        Raises:
            ValueError
        """
        if not 0 <= cpol <= 1 or not 0 <= cpha <= 1:
            raise ValueError('Invalid spisw_config values')
        cmd = struct.pack('>BBB', 26, 2, cpol, cpha)
        return self.send_command(cmd, 'BB')

    def spi_setup(self, nbytes, sck=1, mosi=2, miso=3):
        """Setup bit-bang SPI (PIO numbers to use)

        Args:
            nbytes: Number of bytes
            sck: Clock pin
            mosi: MOSI pin (master out / slave in)
            miso: MISO pin (master in / slave out)
        Raises:
            ValueError
        """
        if not 0 <= nbytes <= 3:
            raise ValueError('Invalid number of bytes')
        if not 1 <= sck <= 6 or not 1 <= mosi <= 6 or not 1 <= miso <= 6:
            raise ValueError('Invalid spisw_setup values')
        cmd = struct.pack('>BBBBB', 28, 3, sck, mosi, miso)
        return self.send_command(cmd, 'BBB')

    def spi_write(self, value, word=False):
        """Bit-bang SPI transfer (send+receive) a byte or a word

        Args:
            value: Data to send (byte/word to transmit)
            word: send a 2-byte word, instead of a byte
        """
        if word:
            cmd = struct.pack('>BBH', 29, 2, value)
            ret = self.send_command(cmd, 'H')[0]
        else:
            cmd = struct.pack('>BBB', 29, 1, value)
            ret = self.send_command(cmd, 'B')[0]
        return ret
