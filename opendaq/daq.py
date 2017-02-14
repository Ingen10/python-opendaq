# !/usr/bin/env python

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

from __future__ import print_function
from __future__ import division
import time
import struct
import array
import serial
from threading import Thread
from enum import IntEnum
from .common import check_stream_crc, mkcmd, parse_command, str2hex, escape_bytes
from .common import LengthError, CRCError
from .experiment import Trigger, ExpMode, DAQStream, DAQBurst, DAQExternal
from .simulator import DAQSimulator
from .models import DAQModel

BAUDS = 115200
MAX_CHANNELS = 4


class CMD(IntEnum):
    AIN = 1
    AIN_CFG = 2
    PIO = 3
    AIN_ALL = 4
    PIO_DIR = 5
    PORT = 7
    PORT_DIR = 9
    PWM_INIT = 10
    PWM_STOP = 11
    PWM_DUTY = 12
    SET_DAC = 13
    CAPTURE_INIT = 14
    CAPTURE_STOP = 15
    GET_CAPTURE = 16
    WAIT_MS = 17
    LED_W = 18
    STREAM_CREATE = 19
    EXTERNAL_CREATE = 20
    BURST_CREATE = 21
    CHANNEL_CFG = 22
    SIGNAL_LOAD = 23
    SET_ANALOG = 24
    STREAM_DATA = 25
    SPISW_CONFIG = 26
    RESET = 27
    SPISW_SETUP = 28
    SPISW_TRANSFER = 29
    EEPROM_WRITE = 30
    EEPROM_READ = 31
    CHANNEL_SETUP = 32
    TRIGGER_SETUP = 33
    GET_TRIGGER_MODE = 34
    GET_STATE_CHANNEL = 35
    GET_CALIB = 36
    SET_CALIB = 37
    RESET_CALIB = 38
    ID_CONFIG = 39
    COUNTER_INIT = 41
    GET_COUNTER = 42
    CHANNEL_FLUSH = 45
    ENCODER_INIT = 50
    ENCODER_STOP = 51
    GET_ENCODER = 52
    ENABLE_CRC = 55
    CHANNEL_DESTROY = 57
    STREAM_START = 64
    STREAM_STOP = 80


class LedColor(IntEnum):
    """Valid LED colors."""
    OFF = 0
    GREEN = 1
    RED = 2
    ORANGE = 3


class DAQ(object):
    """This class represents an OpenDAQ device."""

    def __init__(self, port, debug=False):
        """Class constructor
        :param port: Serial port.
        :param debug: Turn on serial echoing to sdout.
        """
        self.__port = port
        self.__debug = debug
        self.__simulate = (port == 'sim')

        self.__measuring = False
        self.__gain = 0
        self.__pinput = 1
        self.__ninput = 0
        self.__exp = []     # list of experiments
        self.__thread = None

        self.open()

        self.__model = DAQModel.new(*self.get_info())
        self.hw_ver = self.__model.model_str
        self.fw_ver = self.__model.fw_ver
        self.__model.load_dac_calib(self.__read_calib_slot)
        self.__model.load_adc_calib(self.__read_calib_slot)
        self.clear_experiments()

    def open(self):
        """Open the serial port."""
        if self.__port == 'sim':
            self.ser = DAQSimulator(self.__port, BAUDS, timeout=1)
        elif 'simavr' in self.__port:
            self.ser = serial.Serial(self.__port, BAUDS, timeout=10,
                                     rtscts=True, dsrdtr=True)
        else:
            self.ser = serial.Serial(self.__port, BAUDS, timeout=1)
            self.ser.setRTS(0)
            time.sleep(2)

    def close(self):
        """Close the serial port."""
        self.ser.close()

    def send_command(self, command, ret_fmt=None):
        """Build a command packet, send it to the openDAQ and process the
        response.

        :param command: Command string.
        :param ret_fmt: Payload format of the response using python 'struct'
            format characters. I ret_fmt is None, no response is expected.
        :returns: Command ID and arguments of the response.
        :raises: LengthError: The legth of the response is not the expected.
        """
        self.ser.write(command)
        if self.__debug:
            print("SENT:", str2hex(command))

        if ret_fmt is None:
            return

        fmt = '!BB' + ret_fmt
        ret_len = 2 + struct.calcsize(fmt)
        ret = self.ser.read(ret_len)
        if self.__debug:
            print("RECV:", str2hex(ret))

        return parse_command(ret, fmt, ret_len)

    def enable_crc(self, on):
        """Enable/Disable the cyclic redundancy check.

        :param on: Enable/disable CRC checking (bool).
        """
        return self.send_command(mkcmd(CMD.ENABLE_CRC, 'B',
                                       int(bool(on))), 'B')[0]

    def __read_calib_slot(self, slot):
        """Read a calibration slot.

        :param slot_id: Number of the calibration slot.
        :returns:
            - Gain raw correction
            - Offset raw correction
        :raises: ValueError
        """
        return self.send_command(mkcmd(CMD.GET_CALIB, 'B', slot), 'Bhh')[1:]

    def __write_calib_slot(self, slot_id, gain, offset):
        """Write a calibration slot.

        :param slot_id: Number of the calibration slot.
        :param gain: Gain raw correction (signed 16-bit integer).
        :param offset: Offset raw correction (signed 16-bit integer).
        :returns:
            - Slot number
            - Gain raw correction
            - Offset raw correction
        :raises: ValueError
        """
        return self.send_command(mkcmd(CMD.SET_CALIB, 'Bhh', slot_id,
                                       int(gain), int(offset)), 'Bhh')

    def get_dac_calib(self):
        """Get the DAC calibration.

        :returns: List of DAC calibration registers
        """
        return list(self.__model.dac_calib)  # return a copy of the list

    def get_adc_calib(self):
        """Get the ADC calibration.

        :returns: List of ADC calibration registers
        """
        return list(self.__model.adc_calib)  # return a copy of the list

    def set_dac_calib(self, regs):
        """Set the DAC calibration.

        :param regs: A list of CalibReg objects.
        :raises: ValueError, IndexError
        """
        self.__model.write_dac_calib(regs, self.__write_calib_slot)

    def set_adc_calib(self, regs):
        """Set the ADC calibration.

        :param regs: A list of CalibReg objects.
        :raises: ValueError, IndexError
        """
        self.__model.write_adc_calib(regs, self.__write_calib_slot)

    def set_id(self, id):
        """Identify openDAQ device.

        :param id: id number of the device [000:999]
        :raises: ValueError
        """
        if not 0 <= id < 1000:
            raise ValueError("id out of range")

        return self.send_command(mkcmd(CMD.ID_CONFIG, 'I', id), 'BBI')

    @property
    def serial_str(self):
        return self.__model.serial_str

    def get_info(self):
        """Read device information.

        :returns: [hardware_version, firmware_version, device_id]
        """
        return self.send_command(mkcmd(CMD.ID_CONFIG, ''), 'BBI')

    def __str__(self):
        return ("Hardware version: %s\n"
                "Firmware version: %s\n"
                "Serial number: %s" %
                (self.__model.model_str, self.__model.fw_ver,
                 self.__model.serial_str))

    def read_eeprom(self, pos):
        """Read a byte from the EEPROM.

        :param val: value to write.
        :param pos: position in memory.
        :raises: ValueError
        """
        if not 0 <= pos < 254:
            raise ValueError("pos out of range")

        return self.send_command(mkcmd(CMD.EEPROM_READ, 'BB', pos, 1), 'BBB')[2]

    def write_eeprom(self, pos, val):
        """Write a byte in the EEPROM.

        :param id: id number of the device [000:999].
        :raises: ValueError
        """
        if not 0 <= pos < 254:
            raise ValueError("pos out of range")

        return self.send_command(mkcmd(CMD.EEPROM_WRITE, 'BBB', pos, 1, val), 'BBB')

    def set_dac(self, raw, number=1):
        """Set DAC output (raw value).
        Set the raw value of the DAC.

        "param raw: Raw ADC value.
        :raises: ValueError
        """
        self.send_command(mkcmd(CMD.SET_DAC, 'hB', int(round(raw)), number), 'hB')[0]

    def set_analog(self, volts, number=1):
        """Set DAC output (volts).
        Set the output voltage of the DAC.

        :param volts: DAC output value in volts.
        :raises: ValueError
        """
        self.set_dac(self.__model.volts_to_raw(volts, number - 1), number)

    def read_adc(self):
        """Read data from ADC and return the raw value.

        :returns: Raw ADC value.
        """
        return self.send_command(mkcmd(CMD.AIN, ''), 'h')[0]

    def read_analog(self):
        """Read data from ADC in volts.

        :returns: Voltage value.
        """
        value = self.send_command(mkcmd(CMD.AIN, ''), 'h')[0]
        return self.__model.raw_to_volts(value, self.__gain, self.__pinput,
                                         self.__ninput)

    def read_all(self, nsamples=20, gain=0):
        """Read data from all analog inputs

        :param nsamples: Number of samples per data point [0-255] (default=20)
        :param gain: Analog gain (default=1)
        :returns: Values[0:7]: List of the analog reading on each input
        """
        if self.__model.fw_ver < 120:
            raise Warning("Function not implemented in this FW. Try updating")

        values = self.send_command(mkcmd(CMD.AIN_ALL, 'BB', nsamples, gain), '8h')
        return [self.__model.raw_to_volts(v, gain, i, 0) for i, v in
                enumerate(values)]

    def conf_adc(self, pinput=8, ninput=0, gain=0, nsamples=20):
        """Configure the analog-to-digital converter.

        Get the parameters for configure the analog-to-digital converter.

        :param pinput: Positive input [1:8].
        :param ninput: Negative input.
        :param gain: Analog gain.
        :param nsamples: Number of samples per data point [0-255).
        :raises: ValueError
        """

        self.__model.check_adc_settings(pinput, ninput, int(gain))

        if not 0 <= nsamples < 256:
            raise ValueError("samples number out of range")

        self.__gain = int(gain)
        self.__pinput = pinput
        self.__ninput = ninput

        self.send_command(mkcmd(CMD.AIN_CFG, 'BBBB', pinput, ninput,
                                int(gain), nsamples), 'hBBBB')

    def set_led(self, color, number=1):
        """Choose LED status.
        LED switch on (green, red or orange) or switch off.

        :param color: LED color (use :class:`.LedColor`).
        :raises: ValueError
        """
        if not type(color) is LedColor:
            raise ValueError("Invalid color value")

        if not 1 <= number <= self.__model.nleds:
            raise ValueError("Invalid LED number")

        self.send_command(mkcmd(CMD.LED_W, 'BB',
                                color.value, number), 'BB')

    def set_pio(self, number, value):
        """Write PIO output value.
        Set the value of the PIO terminal (0: low, 1: high).

        :param number: PIO number.
        :param value: digital value (0: low, 1: high)
        :raises: ValueError
        """
        self.__model.check_pio(number)

        if value not in [0, 1]:
            raise ValueError("digital value out of range")

        self.send_command(mkcmd(CMD.PIO, 'BB', number,
                                int(bool(value))), 'BB')[1]

    def read_pio(self, number):
        """Read PIO input value (0: low, 1: high).

        :param number: PIO number.
        :returns: Read value.
        :raises: ValueError
        """
        self.__model.check_pio(number)

        return self.send_command(mkcmd(CMD.PIO, 'B', number), 'BB')[1]

    def set_pio_dir(self, number, output):
        """Configure PIO direction.
        Set the direction of a specific PIO terminal (D1-D6).

        :param number: PIO number.
        :param output: PIO direction (0 input, 1 output).
        :raises: ValueError
        """
        self.__model.check_pio(number)

        if output not in [0, 1]:
            raise ValueError("PIO direction out of range")

        self.send_command(mkcmd(CMD.PIO_DIR, 'BB', number,
                                int(bool(output))), 'BB')

    def set_port(self, value):
        """Write all PIO values.
        Set the value of all Dx terminals.

        :param value: Port output byte (bits: 0:low, 1:high).
        :raises: ValueError
        """
        self.__model.check_port(value)
        self.send_command(mkcmd(CMD.PORT, 'B', value), 'B')[0]

    def read_port(self):
        """Read all PIO values.

        :returns: Binary value of the port.
        """
        return self.send_command(mkcmd(CMD.PORT, ''), 'B')[0]

    def set_port_dir(self, output):
        """Configure all PIOs directions.
        Set the direction of all D1-D6 terminals.

        :param output: Port directions byte (bits: 0:input, 1:output).
        :raises: ValueError
        """
        self.__model.check_port(output)
        self.send_command(mkcmd(CMD.PORT_DIR, 'B', output), 'B')

    def spi_config(self, cpol, cpha):
        """Bit-Bang SPI configure (clock properties).

        :param cpol: Clock polarity (clock pin state when inactive).
        :param cpha: Clock phase (leading 0, or trailing 1 edges read).
        :raises: ValueError
        """
        if not 0 <= cpol <= 1 or not 0 <= cpha <= 1:
            raise ValueError("Invalid spisw_config values")

        self.send_command(mkcmd(CMD.SPISW_CONFIG, 'BB', cpol, cpha), 'BB')

    def spi_setup(self, nbytes, sck=1, mosi=2, miso=3):
        """Bit-Bang SPI setup (PIO numbers to use).

        :param nbytes: Number of bytes.
        :param sck: Clock pin.
        :param mosi: MOSI pin (master out / slave in).
        :param miso: MISO pin (master in / slave out).
        :raises: ValueError
        """
        if not 0 <= nbytes <= 3:
            raise ValueError("Invalid number of bytes")
        if not 1 <= sck <= 6 or not 1 <= mosi <= 6 or not 1 <= miso <= 6:
            raise ValueError("Invalid spisw_setup values")

        self.send_command(mkcmd(CMD.SPISW_SETUP, 'BBB', sck, mosi, miso), 'BBB')

    def spi_write(self, value, word=False):
        """Bit-bang SPI transfer (send+receive) a byte or a word.

        :param value: Data to send (byte/word to transmit).
        :param word: send a 2-byte word, instead of a byte.
        :raises: ValueError
        """
        if not 0 <= value <= 65535:
            raise ValueError("Value out of range")

        if word:
            ret = self.send_command(mkcmd(CMD.SPISW_TRANSFER, 'H', value), 'H')[0]
        else:
            ret = self.send_command(mkcmd(CMD.SPISW_TRANSFER, 'B', value), 'B')[0]
        return ret

    def init_counter(self, edge):
        """Initialize the edge counter and configure which edge increments the
        count.

        :param edge: high-to-low (False) or low-to-high (True).
        """
        self.send_command(mkcmd(CMD.COUNTER_INIT, 'B', int(bool(edge))), 'B')[0]

    def get_counter(self, reset):
        """Get the counter value.

        :param reset: reset the counter after perform reading (boolean).
        """
        return self.send_command(mkcmd(CMD.GET_COUNTER, 'B', int(bool(reset))), 'I')[0]

    def init_capture(self, period):
        """Start Capture Mode around a given period.

        :param period: Estimated period of the wave (in microseconds).
        :raises: ValueError
        """
        if not 0 <= period <= 2**32:
            raise ValueError("Period value out of range")

        self.send_command(mkcmd(CMD.CAPTURE_INIT, 'I', period), 'I')[0]

    def stop_capture(self):
        """Stop Capture mode."""
        self.send_command(mkcmd(CMD.CAPTURE_STOP, ''), '')

    def get_capture(self, mode):
        """Get Capture reading for the period length.

        :param mode: Period length (0: Low cycle, 1: High cycle,
            2: Full period)
        :returns:
            - mode
            - period: The period length in microseconds
        :raises: ValueError
        """
        if mode not in [0, 1, 2]:
            raise ValueError("mode value out of range")

        return self.send_command(mkcmd(CMD.GET_CAPTURE, 'B', mode), 'BI')

    def init_encoder(self, resolution):
        """Start Encoder function.

        :param resolution: Maximum number of ticks per round [0:65535].
        :raises: ValueError
        """
        if not 0 <= resolution <= 2**32:
            raise ValueError("resolution value out of range")

        self.send_command(mkcmd(CMD.ENCODER_INIT, 'I', resolution), 'I')[0]

    def get_encoder(self):
        """Get current encoder relative position.

        :returns: Position: The actual encoder value.
        """
        return self.send_command(mkcmd(CMD.GET_ENCODER, ''), 'I')[0]

    def stop_encoder(self):
        """Stop encoder"""
        self.send_command(mkcmd(CMD.ENCODER_STOP, ''), '')

    def init_pwm(self, duty, period):
        """Start PWM output with a given period and duty cycle.

        :param duty: High time of the signal [0:1023](0 always low, 1023 always
            high).
        :param period: Period of the signal (microseconds) [0:65535].
        :raises: ValueError
        """
        if not 0 <= duty < 1024:
            raise ValueError("duty value out of range")

        if not 0 <= period <= 65535:
            raise ValueError("period value out of range")

        self.send_command(mkcmd(CMD.PWM_INIT, 'HH', duty, period), 'HH')

    def stop_pwm(self):
        """Stop PWM"""
        self.send_command(mkcmd(CMD.PWM_STOP, ''), '')

    def __trigger_setup(self, number, mode, value):
        """Change the trigger mode of the DataChannel.

        :param number: Number of the DataChannel.
        :param mode: Trigger mode (use :class:`.Trigger`).
        :param value: Value of the trigger mode.
        :raises: ValueError
        """

        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")

        if not type(mode) is Trigger:
            raise ValueError("Invalid trigger mode")

        if 1 <= mode <= 6 and value not in [0, 1]:
            raise ValueError("Invalid value of digital trigger")

        self.send_command(mkcmd(CMD.TRIGGER_SETUP, 'BBH', number, mode, value), 'BBH')

    def trigger_mode(self, number):
        """Get the trigger mode of the DataChannel.

        :param number: Number of the DataChannel.
        :raises: ValueError
        """

        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")

        mode = self.send_command(mkcmd(CMD.GET_TRIGGER_MODE, 'B', number), 'H')[0]
        return Trigger(mode)

    def get_state_ch(self, number):
        """Get state of the DataChannel.

        :param number: Number of the DataChannel.
        :raises: ValueError
        """

        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")

        return self.send_command(mkcmd(CMD.GET_STATE_CHANNEL, 'B', number), 'H')[0]

    def __conf_channel(self, number, mode, pinput=1, ninput=0, gain=1,
                       nsamples=1):
        """Configure a channel for a generic stream experiment
        (Stream/External/Burst).

        :param number: Select a DataChannel number for this experiment
        :param mode: Define data source or destination (use :class:`.ExpMode`).
        :param pinput: Select Positive/SE analog input [1:8]
        :param ninput: Select Negative analog input.
        :param gain: Select PGA multiplier.
        :param nsamples: Number of samples to calculate the mean for each point
            [0:255].
        :raises: ValueError
        """
        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")

        if not type(mode) is ExpMode:
            raise ValueError("Invalid mode")

        if mode == ExpMode.ANALOG_IN:
            self.__model.check_adc_settings(pinput, ninput, int(gain))

        if not 0 <= nsamples < 256:
            raise ValueError("samples number out of range")

        return self.send_command(
            mkcmd(CMD.CHANNEL_CFG, 'BBBBBB', number, mode.value, pinput,
                  ninput, int(gain), nsamples), 'BBBBBB')

    def __setup_channel(self, number, npoints, continuous=False):
        """Configure the experiment's number of points.

        :param number: Select a DataChannel number for this experiment.
        :param npoints: Total number of points for the experiment
            [0:65536] (0 indicates continuous acquisition).
        :param continuous: Indicates if the experiment is continuous
            - False: run once
            - True: continuous
        :raises: ValueError
        """
        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")

        if not 0 <= npoints < 65536:
            raise ValueError("npoints out of range")

        return self.send_command(mkcmd(CMD.CHANNEL_SETUP, 'BHb', number,
                                       npoints, int(not continuous)), 'BHB')

    def remove_experiment(self, experiment):
        """Delete a single experiment.

        :param experiment: reference of the experiment to remove.
        :raises: ValueError
        """
        nb = experiment.get_parameters()[3]
        if not 1 <= nb <= 4:
            raise ValueError("Invalid reference")
        self.__destroy_channel(nb)
        for i in range(len(self.__exp))[::-1]:
            if self.__exp[i].number == nb:
                del(self.__exp[i])

    def clear_experiments(self):
        """Delete the whole experiment list."""
        for i in range(len(self.__exp))[::-1]:
            self.__destroy_channel(i + 1)
            del(self.__exp[i])

    def __used_channels(self):
        """Returns a list of assigned DataChannels.

        :returns: list of assigned DataChannels.
        """
        return [e.number for e in self.__exp]

    def __first_available(self):
        for i in range(1, MAX_CHANNELS + 1):
            if i not in self.__used_channels():
                return i

    def flush_channel(self, number):
        """Flush the channel.

        :param number: Number of DataChannel to flush.
        :returns: ValueError
        """
        if not 1 <= number <= MAX_CHANNELS:
                raise ValueError("Invalid DataChannel number")

        self.send_command(mkcmd(CMD.CHANNEL_FLUSH, 'B', number), 'B')

    def __destroy_channel(self, number):
        """Command firmware to clear a Datachannel structure.

        :param number: Number of DataChannel structure to clear [0:4] (0: reset
            all DataChannels)
        :raises: ValueError
        """
        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")

        return self.send_command(mkcmd(CMD.CHANNEL_DESTROY, 'B', number), 'B')[0]

    def create_stream(self, mode, *args, **kwargs):
        """Create Stream experiment.

        See the :class:`.DAQStream` class constructor for more info.
        """
        if not type(mode) is ExpMode:
            raise ValueError("Invalid mode")

        index = len(self.__exp)
        if index > 0 and self.__exp[0].__class__ is DAQBurst:
            raise LengthError("Device is configured for a Burst experiment")

        if len(self.__used_channels()) == MAX_CHANNELS:
            raise LengthError("Maximum value of experiments has been reached")

        if mode == ExpMode.ANALOG_OUT:
            chan = 4  # DAC_OUTPUT is fixed at DataChannel 4
            for i in range(index):
                if self.__exp[i].number == chan:
                    if type(self.__exp[i]) is DAQStream:
                        self.__exp[i].number = self.__first_available()
                    else:
                        raise ValueError("DataChannel 4 is being used")
        else:
            chan = self.__first_available()

        self.__exp.append(DAQStream(mode, chan, *args, **kwargs))
        return self.__exp[index]

    def __create_stream(self, number, period):
        """Send a command to the firmware to create a Stream experiment.

        :param number: Assign a DataChannel number for this experiment [1:4].
        :param period: Period of the stream experiment (ms) [1:65536].
        :raises: ValueError
        """
        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")
        if not 1 <= period <= 65535:
            raise ValueError("Invalid period")

        self.send_command(mkcmd(CMD.STREAM_CREATE, 'BH', number, period), 'BH')

    def create_external(self, mode, clock_input, *args, **kwargs):
        """Create External experiment.

        See the :class:`.DAQExternal` class constructor for more info.
        """
        if not type(mode) is ExpMode:
            raise ValueError("Invalid mode")

        index = len(self.__exp)
        if index > 0 and self.__exp[0].__class__ is DAQBurst:
            raise LengthError("Device is configured for a Burst experiment")

        if len(self.__used_channels()) == MAX_CHANNELS:
            raise LengthError("Maximum value of experiments has been reached")

        for i in range(index):
            if self.__exp[i].number == clock_input:
                if type(self.__exp[i]) is DAQStream:
                    self.__exp[i].number = self.__first_available()
                else:
                    raise ValueError("Clock_input is being used by another experiment")

        self.__exp.append(DAQExternal(mode, clock_input, *args, **kwargs))
        return self.__exp[index]

    def __create_external(self, number, edge):
        """Send a command to the firmware to create an External experiment.

        :param number: Assign a DataChannel number for this experiment [1:4].
        :param edge: New data on rising (1) or falling (0) edges [0:1].
        :raises: ValueError
        """
        if not 1 <= number <= MAX_CHANNELS:
            raise ValueError("Invalid DataChannel number")

        if edge not in [0, 1]:
            raise ValueError("Invalid edge")

        return self.send_command(mkcmd(CMD.EXTERNAL_CREATE, 'BB', number, edge), 'BB')

    def create_burst(self, *args, **kwargs):
        """Create Burst experiment.

        See the :class:`.DAQBurst` class constructor for more info.
        """

        if len(self.__exp) > 0:
            raise LengthError("Only one experiment allowed when using burst")

        self.__exp.append(DAQBurst(*args, **kwargs))
        return self.__exp[0]

    def __create_burst(self, period):
        """Send a command to the firmware to create a Burst experiment.

        :param period: Period of the burst experiment (microseconds)
            [100:65535]
        :raises: ValueError
        """
        if not 100 <= period <= 65535:
            raise ValueError("Invalid period")

        return self.send_command(mkcmd(CMD.BURST_CREATE, 'H', period), 'H')

    def __load_signal(self, data, offset=0):
        """Load an array of values in volts to preload DAC output.

        :raises: LengthError: Invalid dada length.
        """
        if not 1 <= len(data) <= 400:
            raise LengthError("Invalid data length")

        self.set_analog(data[0])
        values = [self.__model.volts_to_raw(v, 0) for v in data]
        return self.send_command(mkcmd(CMD.SIGNAL_LOAD, 'h%dh' % len(values),
                                       offset, *values), 'Bh')

    def flush(self):
        """Flush internal buffers."""
        self.ser.flushInput()

    def __read_stream_packet(self):
        packet = self.ser.read(5)
        _, cmd, size, ch = struct.unpack('!HBBB', packet)

        if cmd == CMD.STREAM_DATA:
            body = escape_bytes(self.ser.read(size - 1), (0x7d, 0x7e))

            if self.__debug:
                print("STRM:", str2hex(packet), str2hex(body))
                print(str2hex(body))

            data = struct.unpack('!%dh' % ((size - 4)/2), body[3:])
            return ch, data
        elif cmd == CMD.STREAM_STOP:
            if self.__debug:
                print("STRM:", str2hex(packet))
            return ch, None
        else:
            raise IOError("Invalid stream command: %d", cmd)

    def __read_stream(self):
        """Generator that reads and parses a stream packet at a time.

        :returns: (data, channel)
            - channel: Assigned experiment number.
            - data: Buffer for data points.
        """
        while True:
            # wait for a start byte
            while self.ser.read(1) != chr(0x7e):
                pass
            # read a packet
            try:
                yield self.__read_stream_packet()
            except EOFError:
                break

    @property
    def is_measuring(self):
        """True if any experiment is going on."""
        return self.__measuring

    def start(self):
        """Start all available experiments."""
        if self.__thread and self.__thread.isAlive():
            return

        # setup the openDAQ
        for s in self.__exp:
            if s.__class__ is DAQBurst:
                self.__create_burst(s.period)
            elif s.__class__ is DAQStream:
                self.__create_stream(s.number, s.period)
            else:
                self.__create_external(s.number, s.edge)

            self.__setup_channel(s.number, s.npoints, s.continuous)
            self.__conf_channel(s.number, s.mode, s.pinput,
                                s.ninput, s.gain, s.nsamples)
            self.__trigger_setup(s.number, s.trg_mode, s.trg_value)

            if s.get_mode() == ExpMode.ANALOG_OUT:
                self.__load_signal(*s.get_preload_data())
                break

        self.__measuring = True
        self.send_command(mkcmd(CMD.STREAM_START, ''), '')
        self.__thread = Thread(target=self.__run)
        self.__thread.daemon = True
        self.__thread.start()

    def stop(self, clear=False):
        """Stop all running experiments and exit threads.

        :param clear: If True, the experiment list will be cleared. The
        experiments will no longer be available.
        """
        if self.__thread and self.__thread.isAlive():
            self.send_command(mkcmd(CMD.STREAM_STOP, ''))
            self.__thread.join() # wait for thread to finish

            if clear:
                self.clear_experiments()

    def __run(self):
        """Thread loop.

        Store the experiment data sent by the device after calling start().
        """
        used = self.__used_channels()
        stopped = 0

        for ch, data in self.__read_stream():
            if data is None:
                stopped += 1
                if stopped == len(used):
                    break
            else:
                exp = self.__exp[used.index(ch)]
                exp.add_points(self.__model.raw_to_volts(data, *exp.get_params()))

        self.__measuring = False
