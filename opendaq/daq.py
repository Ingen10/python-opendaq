# !/usr/bin/env python
# !/usr/bin/env python

# Copyright 2015
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
import time
import serial
import threading
from opendaq.common import check_crc, mkcmd, check_stream_crc, LengthError
from opendaq.simulator import DAQSimulator
from opendaq.stream import DAQStream
from opendaq.burst import DAQBurst
from opendaq.external import DAQExternal

BAUDS = 115200
INPUT_MODES = ('ANALOG_INPUT', 'ANALOG_OUTPUT', 'DIGITAL_INPUT',
               'DIGITAL_OUTPUT', 'COUNTER_INPUT', 'CAPTURE_INPUT')
LED_OFF = 0
LED_GREEN = 1
LED_RED = 2
NAK = mkcmd(160, '')

ANALOG_INPUT = 0
ANALOG_OUTPUT = 1
DIGITAL_INPUT = 2
DIGITAL_OUTPUT = 3
COUNTER_INPUT = 4
CAPTURE_INPUT = 5

GAIN_M_X05 = 0
GAIN_M_X1 = 1
GAIN_M_X2 = 2
GAIN_M_X10 = 3
GAIN_M_X100 = 4

GAIN_S_X1 = 0
GAIN_S_X2 = 1
GAIN_S_X4 = 2
GAIN_S_X5 = 3
GAIN_S_X8 = 4
GAIN_S_X10 = 5
GAIN_S_X16 = 6
GAIN_S_X20 = 7

MULTIPLIER_LIST = [1, 2, 4, 5, 8, 10, 16, 20]


class DAQ(threading.Thread):
    def __init__(self, port, debug=False):
        """Class constructor"""
        threading.Thread.__init__(self)
        self.port = port
        self.debug = debug
        self.simulate = (port == 'sim')

        self.__running = False
        self.measuring = False
        self.__stopping = False
        self.gain = 0
        self.pinput = 1
        self.open()

        info = self.get_info()
        self.__hw_ver = 'm' if info[0] == 1 else 's'
        self.gains, self.offsets = self.get_cal()
        self.dac_gain, self.dac_offset = self.get_dac_cal()

        self.experiments = [] 
        self.preload_data = None

    def open(self):
        """Open the serial port
        Configure serial port to be opened."""
        if self.simulate:
            self.ser = DAQSimulator(self.port, BAUDS, timeout=1)
        else:
            self.ser = serial.Serial(self.port, BAUDS, timeout=1)
            self.ser.setRTS(0)
            time.sleep(2)

    def close(self):
        """Close the serial port"""
        self.ser.close()

    def send_command(self, command, ret_fmt):
        """Build a command packet, send it to the openDAQ and process the
        response

        Args:
            cmd: Command string
            ret_fmt: Payload format of the response using python
            'struct' format characters
        Returns:
            Command ID and arguments of the response
        Raises:
            LengthError: The legth of the response is not the expected
        """
        fmt = '!BB' + ret_fmt
        ret_len = 2 + struct.calcsize(fmt)
        self.ser.write(command)
        ret = self.ser.read(ret_len)
        if self.debug:
            print 'Command:  ',
            for c in command:
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
        return self.send_command(mkcmd(39, ''), 'BBI')

    def device_info(self):
        """Return device configuration

        Returns:
            [hardware version, firmware version, device ID number]
        """
        hv, fv, serial = self.get_info()
        print "Hardware Version: ", "[M]" if hv == 1 else "[S]"
        print "Firmware Version:", fv
        print "Serial number: OD" + ("M08" if hv == 1
                                     else "S08") + str(serial).zfill(3) + "5"

    def hw_ver(self):
        return self.__hw_ver

    def read_adc(self):
        """Read data from ADC and return the raw value

        Returns:
            Raw ADC value
        """
        return self.send_command(mkcmd(1, ''), 'h')[0]

    def read_analog(self):
        """Read data from ADC in volts

        Returns:
            Voltage value
        """
        value = self.send_command(mkcmd(1, ''), 'h')[0]
        # Raw value to voltage->
        index = self.gain + 1 if self.__hw_ver == 'm' else self.pinput
        value *= self.gains[index]
        value = -value/1e5 if self.__hw_ver == 'm' else value/1e4
        value = (value + self.offsets[index])/1e3
        return value

    def read_all(self, nsamples=20, gain=0):
        """Read data from all analog inputs

        Args:
            nsamples: Number of samples per data point [0-255] (default=20)
            gain: Analog gain
                openDAQ[M]= [0:4] (x1/3, x1, x2, x10, x100)
                openDAQ[S]= [0:7] (x1,x2,x4,x5,x8,x10,x16,x20)
                (default=1)
        Returns:
            Values[0:7]: List of the analog reading on each input
        """

        self.gain = gain
        values = self.send_command(mkcmd(4, 'BB', nsamples, gain), '8h')
        if self.__hw_ver == 'm':
            a = -self.gains[self.gain + 1]/1e5
            b = self.offsets[self.gain + 1]
            val = [(v*a+b)/1e3 for v in values]
        else:
            val = [(v*self.gains[i+1]/1e4+self.offsets[i+1])/1e3
                   for i, v in enumerate(values)]
        return val

    def conf_adc(self, pinput=8, ninput=0, gain=0, nsamples=20):
        """
        Configure the analog-to-digital converter.

        Get the parameters for configure the analog-to-digital
        converter.

        Args:
            pinput: Positive input [1:8]
            ninput: Negative input
                openDAQ[M]= [0, 5, 6, 7, 8, 25]
                openDAQ[S]= [0,1:8] (must be 0 or pinput-1)
            gain: Analog gain
                openDAQ[M]= [0:4] (x1/3, x1, x2, x10, x100)
                openDAQ[S]= [0:7] (x1,x2,x4,x5,x8,x10,x16,x20)
            nsamples: Number of samples per data point [0-255)
        Raises:
            ValueError: Values out of range
        """
        if not 1 <= pinput <= 8:
            raise ValueError("positive input out of range")

        if self.__hw_ver == 'm' and ninput not in [0, 5, 6, 7, 8, 25]:
            raise ValueError("negative input out of range")

        if self.__hw_ver == 's' and ninput != 0 and (
            pinput % 2 == 0 and ninput != pinput - 1 or
                pinput % 2 != 0 and ninput != pinput + 1):
                    raise ValueError("negative input out of range")

        if self.__hw_ver == 'm' and not 0 <= gain <= 4:
            raise ValueError("gain out of range")

        if self.__hw_ver == 's' and not 0 <= gain <= 7:
            raise ValueError("gain out of range")

        if not 0 <= nsamples < 255:
            raise ValueError("samples number out of range")

        self.gain = gain

        if self.__hw_ver == 's' and ninput != 0:
            self.pinput = (pinput - 1)/2 + 9
        else:
            self.pinput = pinput

        return self.send_command(mkcmd(2, 'BBBB', pinput,
                                       ninput, gain, nsamples), 'hBBBB')

    def enable_crc(self, on):
        """Enable/Disable the cyclic redundancy check

        Args:
            on: Enable CRC
        Raises:
            ValueError: on value out of range
        """
        if on not in [0, 1]:
            raise ValueError("on value out of range")

        return self.send_command(mkcmd(55, 'B', on), 'B')[0]

    def set_led(self, color):
        """Choose LED status.
        LED switch on (green, red or orange) or switch off.

        Args:
            color: LED color (0:off, 1:green, 2:red, 3:orange)
        Raises:
            ValueError: Invalid color number
        """
        if not 0 <= color <= 3:
            raise ValueError('Invalid color number')

        return self.send_command(mkcmd(18, 'B', color), 'B')[0]

    def __volts_to_raw(self, volts):
        """Convert a value in volts to a raw value.
        Device calibration values are used for the calculation.

        openDAQ[M] range: -4.096 V to +4.096 V
        openDAQ[S] range: 0 V to +4.096 V

        Args:
            volts: value to convert to raw
        Returns:
            Raw value
        Raises:
            ValueError: DAC voltage out of range
        """
        value = int(round(volts*1000))

        if self.__hw_ver == 'm' and not -4096 <= value < 4096:
            raise ValueError('DAC voltage out of range')
        elif self.__hw_ver == 's' and not 0 <= value < 4096:
            raise ValueError('DAC voltage out of range')

        data = 2*(value * self.dac_gain/1000.0 + self.dac_offset + 4096)
        if self.__hw_ver == 's':
            data = max(0, min(data, 65535))  # clamp value

        return data

    def set_analog(self, volts):
        """Set DAC output voltage (millivolts value).
        Set the output voltage value between the voltage hardware limits.
        Device calibration values are used for the calculation.

        openDAQ[M] range: -4.096 V to +4.096 V

        openDAQ[S] range: 0 V to +4.096 V

        Args:
            volts: New DAC output value in millivolts
        Raises:
            ValueError: DAC voltage out of range
        """
        if self.__hw_ver == 'm' and not -4096 <= volts < 4096:
            raise ValueError('DAC voltage out of range')
        elif self.__hw_ver == 's' and not 0 <= volts < 4096:
            raise ValueError('DAC voltage out of range')

        data = self.__volts_to_raw(volts)
        self.set_dac(data)

    def set_dac(self, raw):
        """Set DAC output (binary value)

        Set the raw value into DAC without data conversion.

        Args:
            raw: RAW binary ADC data value.
        Raises:
            ValueError: DAC voltage out of range
        """
        value = int(round(raw))
        if (self. __hw_ver == 'm' and not 0 <= value < 16384) or (
                self. __hw_ver == 's' and not 0 <= value < 65536):
                    raise ValueError('DAC value out of range')

        return self.send_command(mkcmd(24, 'H', value), 'h')[0]

    def set_port_dir(self, output):
        """Configure all PIOs directions.
        Set the direction of all D1-D6 terminals.

        Args:
            output: Port directions byte (bits: 0:input, 1:output)
        Raises:
            ValueError: output value out of range
        """
        if not 0 <= output < 64:
            raise ValueError("output value out of range")

        return self.send_command(mkcmd(9, 'B', output), 'B')[0]

    def set_port(self, value):
        """Write all PIO values
        Set the value of all D1-D6 terminals.
        Args:
            value: Port output byte (bits: 0:low, 1:high)
        Returns:
            Real value of the port. Output pin as fixed in value\
                input pin refresh with current state.
        Raises:
            ValueError: port output byte out of range
        """
        if not 0 <= value < 64:
            raise ValueError("port output byte out of range")

        return self.send_command(mkcmd(7, 'B', value), 'B')[0]

    def set_pio_dir(self, number, output):
        """Configure PIO direction
        Set the direction of a specific PIO terminal (D1-D6).

        Args:
            number: PIO number [1:6]
            output: PIO direction (0 input, 1 output)
        Raises:
            ValueError: Invalid PIO number
        """
        if not 1 <= number <= 6:
            raise ValueError('Invalid PIO number')

        if output not in [0, 1]:
            raise ValueError("PIO direction out of range")

        return self.send_command(mkcmd(5, 'BB', number,
                                       int(bool(output))), 'BB')

    def set_pio(self, number, value):
        """Write PIO output value
        Set the value of the PIO terminal (0: low, 1: high).

        Args:
            number: PIO number (1-6)
            value: digital value (0: low, 1: high)
        Raises:
            ValueError: Invalid PIO number
        """
        if not 1 <= number <= 6:
            raise ValueError('Invalid PIO number')

        if value not in [0, 1]:
            raise ValueError("digital value out of range")

        return self.send_command(mkcmd(3, 'BB', number,
                                       int(bool(value))), 'BB')

    def init_counter(self, edge):
        """Initialize the edge Counter
        Configure which edge increments the count:
        Low-to-High (1) or High-to-Low (0).
        Args:
            edge: high-to-low (0) or low-to-high (1)
        Raises:
            ValueError: edge value out of range
        """
        if edge not in [0, 1]:
            raise ValueError("edge value out of range")

        return self.send_command(mkcmd(41, 'B', edge), 'B')[0]

    def get_counter(self, reset):
        """Get the counter value

        Args:
            reset: reset the counter after perform reading (>0: reset)
        Raises:
            ValueError: reset value out of range
        """
        if not 0 <= reset <= 255:
            raise ValueError("reset value out of range")

        return self.send_command(mkcmd(42, 'B', reset), 'H')[0]

    def init_capture(self, period):
        """Start Capture mode around a given period

        Args:
            period: estimated period of the wave (in microseconds)
        Raises:
            ValueError: period out of range
        """
        if not 0 <= period <= 65535:
            raise ValueError("period out of range")

        return self.send_command(mkcmd(14, 'H', period), 'H')[0]

    def stop_capture(self):
        """Stop Capture mode
        """
        self.send_command(mkcmd(15, ''), '')

    def get_capture(self, mode):
        """Get Capture reading for the period length
        Low cycle, High cycle or Full period.
        Args:
            mode: Period length
                0: Low cycle
                1: High cycle
                2: Full period
        Returns:
            mode
            Period: The period length in microseconds
        Raises:
            ValueError: mode value out of range
        """
        if mode not in [0, 1, 2]:
            raise ValueError("mode value out of range")

        return self.send_command(mkcmd(16, 'B', mode), 'BH')

    def init_encoder(self, resolution):
        """Start Encoder function

        Args:
            resolution: Maximum number of ticks per round [0:65535]
        Raises:
            ValueError: resolution value out of range
        """
        if not 0 <= resolution <= 65535:
            raise ValueError("resolution value out of range")

        return self.send_command(mkcmd(50, 'B', resolution), 'B')[0]

    def get_encoder(self):
        """Get current encoder relative position

        Returns:
            Position: The actual encoder value.
        """
        return self.send_command(mkcmd(52, ''), 'H')[0]

    def stop_encoder(self):
        """Stop encoder"""
        self.send_command(mkcmd(51, ''), '')

    def init_pwm(self, duty, period):
        """Start PWM output with a given period and duty cycle

        Args:
            duty: High time of the signal [0:1023](0 always low,\
                 1023 always high)
            period: Period of the signal (microseconds) [0:65535]
        Raises:
            ValueError: Values out of range
        """
        if not 0 <= duty < 1024:
            raise ValueError("duty value out of range")

        if not 0 <= period <= 65535:
            raise ValueError("period value out of range")

        return self.send_command(mkcmd(10, 'HH', duty, period), 'HH')

    def stop_pwm(self):
        """Stop PWM"""
        self.send_command(mkcmd(11, ''), '')

    def __get_calibration(self, gain_id):
        """
        Read device calibration for a given analog configuration

        Gets calibration gain and offset for the corresponding analog
        configuration

        Args:
            gain_id: analog configuration
            (0:5 for openDAQ [M])
            (0:16 for openDAQ [S])
        Returns:
            gain_id
            Gain (x100000[M] or x10000[S])
            Offset
        Raises:
            ValueError: gain_id out of range
        """
        if (self.__hw_ver == 'm' and not 0 <= gain_id <= 5) or (
                self.__hw_ver == 's' and not 0 <= gain_id <= 16):
                    raise ValueError("gain_id out of range")

        return self.send_command(mkcmd(36, 'B', gain_id), 'BHh')

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
        _range = 6 if self.__hw_ver == "m" else 17
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
        Raises:
            ValueError: Values out of range
        """
        if (self.__hw_ver == 'm' and not 0 <= gain_id <= 5) or (
                self.__hw_ver == 's' and not 0 <= gain_id <= 16):
                    raise ValueError("gain_id out of range")

        if not 0 <= gain < 65536:
            raise ValueError("gain out of range")

        if not -32768 <= offset < 32768:
            raise ValueError("offset out of range")

        return self.send_command(mkcmd(37, 'BHh', gain_id,
                                       gain, offset), 'BHh')

    def set_cal(self, gains, offsets, flag):
        """
        Set device calibration

        Args:
            gains: Gain multiplied by 100000 ([M]) or 10000 ([S])
            offsets: Offset raw value (-32768 to 32768)
            flag: 'M', 'SE' or 'DE'
        Raises:
            ValueError: Values out of range
        """
        for gain in gains:
            if not 0 <= gain < 65536:
                raise ValueError("gain out of range")

        for offset in offsets:
            if not -32768 <= offset < 32768:
                raise ValueError("offset out of range")

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

    def set_dac_cal(self, gain, offset):
        """
        Set DAC calibration

        Args:
            gain: Gain multiplied by 100000 ([M]) or 10000 ([S])
            ofset: Offset raw value (-32768 to 32678)
        Raises:
            ValueError: Values out of range
        """
        if not 0 <= gain < 65536:
            raise ValueError("gain out of range")

        if not -32768 <= offset < 32768:
            raise ValueError("offset out of range")

        self.__set_calibration(0, gain, offset)

    def __raw_to_volts(self, raw, experiment):
        """Convert a raw value to a value in volts.

        Args:
            raw: Value to convert to volts
            experiment: DataChannel number of this experiment
        """
        if not 0 <= experiment <= 3:
            raise ValueError('Invalid experiment number')

        gain_id, pinput, ninput, number = (
            self.experiments[experiment].get_parameters())

        if self.__hw_ver == 'm':
            gain = self.gains[gain_id + 1]
            offset = self.offsets[gain_id + 1]

            volts = float(raw)
            volts *= gain
            volts = -volts/1e5
            volts = (volts + offset)/1e3

        if self.__hw_ver == 's':
            n = pinput
            if ninput != 0:
                n += 8

            gain = self.gains[n]
            offset = self.offsets[n]
            volts = ((float(raw * gain))/1e4 + offset)
            volts /= MULTIPLIER_LIST[gain_id]
            volts /= 1000.0

        return volts

    def set_id(self, id):
        """
        Identify openDAQ device

        Args:
            id: id number of the device [000:999]
        Raises:
            ValueError: id out of range
        """
        if not 0 <= id < 1000:
            raise ValueError('id out of range')

        return self.send_command(mkcmd(39, 'I', id), 'bbI')

    def spi_config(self, cpol, cpha):
        """Bit-Bang SPI configure (clock properties)

        Args:
            cpol: Clock polarity (clock pin state when inactive)
            cpha: Clock phase (leading 0, or trailing 1 edges read)
        Raises:
            ValueError: Invalid spisw_config values
        """
        if not 0 <= cpol <= 1 or not 0 <= cpha <= 1:
            raise ValueError('Invalid spisw_config values')

        return self.send_command(mkcmd(26, 'BB', cpol, cpha), 'BB')

    def spi_setup(self, nbytes, sck=1, mosi=2, miso=3):
        """Bit-Bang SPI setup (PIO numbers to use)

        Args:
            nbytes: Number of bytes
            sck: Clock pin
            mosi: MOSI pin (master out / slave in)
            miso: MISO pin (master in / slave out)
        Raises:
            ValueError: Invalid values
        """
        if not 0 <= nbytes <= 3:
            raise ValueError('Invalid number of bytes')
        if not 1 <= sck <= 6 or not 1 <= mosi <= 6 or not 1 <= miso <= 6:
            raise ValueError('Invalid spisw_setup values')

        return self.send_command(mkcmd(28, 'BBB', sck, mosi, miso), 'BBB')

    def spi_write(self, value, word=False):
        """Bit-bang SPI transfer (send+receive) a byte or a word

        Args:
            value: Data to send (byte/word to transmit)
            word: send a 2-byte word, instead of a byte
        Raises:
            ValueError: Value out of range
        """
        if not 0 <= value <= 65535:
            raise ValueError("value out of range")

        if word:
            ret = self.send_command(mkcmd(29, 'H', value), 'H')[0]
        else:
            ret = self.send_command(mkcmd(29, 'B', value), 'B')[0]
        return ret

    def __conf_channel(
            self, number, mode, pinput=1, ninput=0, gain=1, nsamples=1):
        """
        Configure a channel for a generic stream experiment.
        (Stream/External/Burst).

        Args:
            - number: Select a DataChannel number for this experiment
            - mode: Define data source or destination [0:5]:
                0) ANALOG_INPUT
                1) ANALOG_OUTPUT
                2) DIGITAL_INPUT
                3) DIGITAL_OUTPUT
                4) COUNTER_INPUT
                5) CAPTURE_INPUT

            - pinput: Select Positive/SE analog input [1:8]
            - ninput: Select Negative analog input:
                openDAQ[M]= [0, 5, 6, 7, 8, 25]
                openDAQ[S]= [0,1:8] (must be 0 or pinput-1)

            - gain: Select PGA multiplier.
                In case of openDAQ [M]:
                    0. x1/2
                    1. x1
                    2. x2
                    3. x10
                    4. x100

                In case of openDAQ [S]:
                    0. x1
                    1. x2
                    2. x4
                    3. x5
                    4. x8
                    5. x10
                    6. x16
                    7. x20

            - nsamples: Number of samples to calculate the mean for each point\
                 [0:255].
        Raises:
            ValueError: Values out of range
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')

        if type(mode) == int and not 0 <= mode <= 5:
            raise ValueError('Invalid mode')

        if type(mode) == str:
            if mode in INPUT_MODES:
                mode = INPUT_MODES.index(mode)
            else:
                raise ValueError('Invalid mode')

        if not 0 <= pinput <= 8:
            raise ValueError('pinput out of range')

        if self.__hw_ver == 'm' and ninput not in [0, 5, 6, 7, 8, 25]:
            raise ValueError("negative input out of range")

        if self.__hw_ver == 's' and ninput != 0 and (
            pinput % 2 == 0 and ninput != pinput - 1 or
                pinput % 2 != 0 and ninput != pinput + 1):
                    raise ValueError("negative input out of range")

        if self.__hw_ver == 'm' and not 0 <= gain <= 4:
            raise ValueError("gain out of range")

        if self.__hw_ver == 's' and not 0 <= gain <= 7:
            raise ValueError("gain out of range")

        if not 0 <= nsamples < 255:
            raise ValueError("samples number out of range")

        return self.send_command(mkcmd(22, 'BBBBBB', number, mode, pinput,
                                       ninput, gain, nsamples), 'BBBBBB')

    def __setup_channel(self, number, npoints, continuous=False):
        """
        Configure the experiment's number of points

        Args:
            number: Select a DataChannel number for this experiment
            npoints: Total number of points for the experiment
            [0:65536] (0 indicates continuous acquisition)
            continuous: Indicates if experiment is continuous
                False run once
                True continuous
        Raises:
            ValueError: Values out of range
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')

        if not 0 <= npoints < 65536:
            raise ValueError('npoints out of range')

        return self.send_command(mkcmd(32, 'BHb', number,
                                       npoints, int(not continuous)), 'BHB')

    def remove_experiment(self, experiment):
        """
        Delete a single experiment

        Args:
            experiment: reference of the experiment to remove
        Raises:
            ValueError: Invalid reference
        """
        nb = experiment.get_parameters()[3]
        if not 1 <= nb <= 4:
            raise ValueError('Invalid reference')
        self.__destroy_channel(nb)
        for i in range(len(self.experiments))[::-1]:
            if self.experiments[i].number == nb:
                del(self.experiments[i])
        
    def clear_experiments(self):
        """
        Delete the whole experiment list

        Args:
            None
        """
        for i in range(len(self.experiments))[::-1]:
            self.__destroy_channel(i+1)
            del(self.experiments[i])

    def dchanindex(self):
        """
        Check which internal DataChannels are used or available

        Args:
            None
        Returns:
            available: list of free DataChannels
            used: list of asigned DataChannels
        """
        used = [e.number for e in self.experiments]
        available = [i for i in range(1, 5) if i not in used]
        return available, used
            
    def __destroy_channel(self, number):
        """
        Command firmware to clear a Datachannel structure

        Args:
            number: Number of DataChannel structure to clear
            [0:4] (0: reset all DataChannels)
        Raises:
            ValueError: Invalid number
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')

        return self.send_command(mkcmd(57, 'B', number), 'B')[0]

    def create_stream(self, mode, *args, **kwargs):
        """
        Create Stream experiment
        See class constructor for more info
        """

        available, used = self.dchanindex()

        index = len(self.experiments)
        
        if index>0 and type(self.experiments[0]) is DAQBurst:
            raise LengthError('Device is configured for a Burst experiment')

        if len(available) == 0:
            raise LengthError('Only 4 experiments available at a time')

        if mode == ANALOG_OUTPUT:
            chan = 4 # DAC_OUTPUT is fixed at DataChannel 4
            for i in range(index):
                if self.experiments[i].number == chan: 
                    if type(self.experiments[i]) is DAQStream:
                        self.experiments[i].number=available[0]
                    else:
                        raise ValueError(
                            'DataChannel 4 is being used by another experiment')
        else:
            chan = available[0]

        self.experiments.append(DAQStream(mode, chan, *args, **kwargs))
        return self.experiments[index]

    def __create_stream(self, number, period):
        """
        Send a command to the firmware to create Stream experiment

        Args:
            number: Assign a DataChannel number for this experiment [1:4]
            period: Period of the stream experiment
            (milliseconds) [1:65536]
        Raises:
            ValueError: Invalid values
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')
        if not 1 <= period <= 65535:
            raise ValueError('Invalid period')

        return self.send_command(mkcmd(19, 'BH', number, period), 'BH')

    def create_external(self, mode, clock_input, *args, **kwargs):
        """
        Create External experiment
        See class constructor for more info
        """
        available, used = self.dchanindex()

        index = len(self.experiments)
        
        if index>0 and type(self.experiments[0]) is DAQBurst:
            raise LengthError('Device is configured for a Burst experiment')

        if len(available) == 0:
            raise LengthError('Only 4 experiments available at a time')

        for i in range(index):
            if self.experiments[i].number == clock_input:
                if type(self.experiments[i]) is DAQStream:
                    self.experiments[i].number=available[0]
                else:
                    raise ValueError(
                        'Clock_input is being used by another experiment')

        self.experiments.append(DAQExternal(mode, clock_input, *args, **kwargs))      
        return self.experiments[index]

    def __create_external(self, number, edge):
        """
        Send a command to the firmware to create External experiment

        Args:
            number: Assign a DataChannel number for this experiment [1:4]
            edge: New data on rising (1) or falling (0) edges [0:1]
        Raises:
            ValueError: Invalid values
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')

        if edge not in [0, 1]:
            raise ValueError('Invalid edge')

        return self.send_command(mkcmd(20, 'BB', number, edge), 'BB')

    def create_burst(self, *args, **kwargs):
        """
        Create Burst experiment

        """

        if len(self.experiments) > 0:
                raise ValueError(
                    'Only 1 experiment available at a time if using burst')

        self.experiments.append(DAQBurst(*args, **kwargs))
        return self.experiments[0]

    def __create_burst(self, period):
        """
        Send a command to the firmware to create Burst experiment

        Args:
            period: Period of the burst experiment
            (microseconds) [100:65535]
        Raises:
            ValueError: Invalid period
        """
        if not 100 <= period <= 65535:
            raise ValueError('Invalid period')

        return self.send_command(mkcmd(21, 'H', period), 'H')

    def __load_signal(self):
        """
        Load an array of values in volts to preload DAC output

        Raises:
            LengthError: Invalid dada length
        """
        if not 1 <= len(self.preload_data) <= 400:
            raise LengthError('Invalid data length')

        values = []
        for volts in self.preload_data:
            raw = self.__volts_to_raw(volts)
            '''
            if self.__hw_ver == "s":
                raw *= 2'''

            values.append(raw)
        return self.send_command(mkcmd(23, 'h%dH' % len(values),
                                       self.preload_offset, *values), 'Bh')

    def flush(self):
        """
        Flush internal buffers
        """
        self.ser.flushInput()

    def get_stream(self, data, channel):
        """Get stream from serial connection

        Args:
            data: Data buffer
            channel: Experiment number

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
        head = struct.unpack('!b', ret)
        if head[0] != 0x7E:
            data.append(head[0])
            return 2
        # Get header
        while len(self.header) < 8:
            ret = self.ser.read(1)
            char = struct.unpack('!B', ret)
            if char[0] == 0x7D:
                ret = self.ser.read(1)
                char = struct.unpack('!B', ret)
                tmp = char[0] | 0x20
                self.header.append(tmp)
            else:
                self.header.append(char[0])
            if len(self.header) == 3 and self.header[2] == 80:
                # openDAQ sent a stop command
                ret = self.ser.read(2)
                char, ch = struct.unpack('!BB', ret)
                channel.append(ch-1)
                return 3
        self.data_length = self.header[3] - 4
        while len(self.data) < self.data_length:
            ret = self.ser.read(1)
            char = struct.unpack('!B', ret)
            if char[0] == 0x7D:
                ret = self.ser.read(1)
                char = struct.unpack('!B', ret)
                tmp = char[0] | 0x20
                self.data.append(tmp)
            else:
                self.data.append(char[0])
        for i in range(0, self.data_length, 2):
            value = (self.data[i] << 8) | self.data[i+1]
            if value >= 32768:
                value -= 65536
            data.append(int(value))
        check_stream_crc(self.header, self.data)
        channel.append(self.header[4]-1)
        return 1

    def is_measuring(self):
        """Return True if system is measuring
        """
        return self.measuring

    def start(self):
        """
        Start all available experiments
        """
        for s in self.experiments:
            if s.__class__ is DAQBurst:
                self.__create_burst(s.period)
            elif s.__class__ is DAQStream:
                self.__create_stream(s.number, s.period)
            else:  # External
                self.__create_external(s.number, s.edge)
            self.__setup_channel(s.number, s.npoints, s.continuous)
            self.__conf_channel(s.number, s.mode, s.pinput,
                                s.ninput, s.gain, s.nsamples)

            if (s.get_mode() == ANALOG_OUTPUT):
                pr_data, pr_offset = s.get_preload_data()
                for i in range(len(pr_data)):
                    self.preload_data = pr_data[i]
                    self.preload_offset = pr_offset[i]
                    self.__load_signal()
                break

        self.send_command(mkcmd(64, ''), '')

        if not self.__running:
            try:
                threading.Thread.start(self)
            except:
                pass
        self.__running = True
        self.measuring = True


    def stop(self):
        """
        Stop all __running experiments and exit threads
        """
        self.measuring = False
        self.__running = False
        self.__stopping = True
        while True:
            try:
                self.send_command(mkcmd(80, ''), '')
                break
            except:
                time.sleep(0.2)
                self.flush()

    def halt(self):
        self.measuring = False
        while True:
            try:
                self.send_command(mkcmd(80, ''), '')
                break
            except:
                time.sleep(0.2)
                self.flush()

    def run(self):
        while True:
            while self.__running:
                if self.measuring:
                    data = []
                    channel = []
                    result = self.get_stream(data, channel)
                    if result == 1:
                        # data available
                        available, used = self.dchanindex()
                        for i in range(len(data)):
                            whichexp = used.index(channel[i]+1)
                            self.experiments[whichexp].add_point(
                                self.__raw_to_volts(data[i], whichexp))

                    elif result == 3:
                        # stop received
                        self.halt()
                else:
                    time.sleep(0.2)

            if self.__stopping:
                break
