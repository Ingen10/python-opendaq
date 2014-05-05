import unittest
from mock import Mock, patch
import struct
import serial

from opendaq import DAQ
from opendaq.common import mkcmd, crc


class TestDAQLimitValues(unittest.TestCase):
    def setUp(self):
        '''
        Connect to openDAQ.
        Initial setup.
        '''
        self.daq = DAQ("COM3")
        self.hw_ver = self.daq.hw_ver

    def tearDown(self):
        '''
        Disconnect openDAQ
        '''
        self.daq.close()

    def test_set_led(self):
        '''
        set_led(color)
        color = (0 - 3)
        '''
        for color in range(4):
            with patch(
                'serial.Serial.read',
                    Mock(return_value=mkcmd(18, 'b', color))):
                        with patch('serial.Serial.write', Mock()):
                            self.daq.set_led(color)
                            cmd = struct.pack('!BBB', 18, 1, color)
                            packet = crc(cmd) + cmd
                            serial.Serial.write.assert_called_with(packet)

    def test_set_led_error(self):
        '''
        set_led(color) -> ValueError
        color = (-1, 4)
        '''
        self.assertRaises(ValueError, self.daq.set_led, -1)
        self.assertRaises(ValueError, self.daq.set_led, 4)

    """
    def test_conf_adc(self):
        '''
        conf_adc(pinput, ninput, gain, nsamples)

        pinput = [1-8]
        ninput (S) = (0, [1-8] and ninput = pinput +- 1 (pair))
        ninput (M) = (0, 5, 6, 7, 8, 25)
        gain (S) = [0 - 4]
        gain (M) = [0 - 7]
        nsamples = (0, 1, 253, 254)
        '''
        pinputs = range(1,9)
        ninputs_m = (range(5,9) + [25]) * 2
        gains_s = range (5) * 2
        gains_m = range(8)
        nsampless = (range(2) + range(253,255)) * 2

        if self.hw_ver == 's':
            for pinput, gain, nsamples in zip(pinputs, gains_s, nsampless):
                ninput = pinput + 1 if pinput % 2 else pinput - 1
                with patch(
                'serial.Serial.read',
                    Mock(return_value=mkcmd(2, 'bbbb', pinput, ninput, gain, nsamples))):
                        with patch('serial.Serial.write', Mock()):
                            self.daq.conf_adc(pinput, ninput, gain, nsamples)
                            cmd = struct.pack('!BBBBBB', 2, 4, pinput, ninput, gain, nsamples)
                            packet = crc(cmd) + cmd
                            serial.Serial.write.assert_called_with(packet)

                ninput = 0
                self.daq.conf_adc(pinput, ninput, gain, nsamples)

        elif self.hw_ver == 'm':
            for pinput, ninput, gain, nsamples in zip(pinputs, ninputs_m, gains_m, nsampless):
                self.daq.conf_adc(pinput, ninput, gain, nsamples)
                ninput = 0
                self.daq.conf_adc(pinput, ninput, gain, nsamples)

    def test_conf_adc_error(self):
        '''
        conf_adc(pinput, ninput, gain, nsamples) -> ValueError

        pinput = (0, 9)
        ninput (S) = (-1, 9, [1-8] and ninput != pinput +- 1, [1-8] and
            ninput = pinput +- 1 (not pair))
        ninput (M) = (-1, 1, 4, 9, 24, 26)        gain (S) = (-1, 5)
        gain (M) = (-1, 8)
        nsamples = (-1, 255)
        '''

    def test_enable_crc(self):
        '''
        enable_crc(on)

        on = (0, 1)
        '''

    def test_enable_crc_error(self):
        '''
        enable_crc(on) -> ValueError

        on = (-1, 2)
        '''

    def test___volts_to_raw(self):
        '''
        __volts_to_raw(volts)

        volts (S) = (0, 4.095)
        volts (M) = (-4.096, 4.095)
        '''

    def test___volts_to_raw_error(self):
        '''
        __volts_to_raw(volts) -> ValueError

        volts (S) = (-0.001, 4.096)
        volts (M) = (-4.097, 4.096)
        '''

    def test_set_analog(self):
        '''
        set_analog(volts)

        volts (S) = (0, 4095)
        volts (M) = (-4096, 4095)
        '''

    def test_set_analog_error(self):
        '''
        set_analog(volts) -> ValueError

        volts (S) = (-1, 4096)
        volts (M) = (-4097, 4096)
        '''

    def test_set_dac(self):
        '''
        set_dac(raw)

        raw (S) = (0, 65535)
        raw (M) = (0, 16383)
        '''

    def test_set_dac_error(self):
        '''
        set_dac(raw) -> ValueError

        raw (S) = (-1, 65536)
        raw (M) = (-1, 16384)
        '''

    def test_set_port_dir(self):
        '''
        set_port_dir(output)

        output = (0, 63)
        '''

    def test_set_port_dir_error(self):
        '''
        set_port_dir(output) -> ValueError

        output = (-1, 64)
        '''

    def test_set_port(self):
        '''
        set_port(value)

        value = (0, 63)
        '''

    def test_set_port_error(self):
        '''
        set_port(value) -> ValueError

        value = (-1, 64)
        '''

    def test_set_pio_dir(self):
        '''
        set_pio_dir(number, output)

        number = (1, 6)
        output = (0, 1)
        '''

    def test_set_pio_dir_error(self):
        '''
        set_pio_dir(number, output) -> ValueError

        number = (0, 7)
        output = (-1, 2)
        '''

    def test_set_pio(self):
        '''
        set_pio(number, value)

        number = (1, 6)
        output = (0, 1)
        '''

    def test_set_pio_error(self):
        '''
        set_pio(number, value) -> ValueError

        number = (0, 7)
        output = (-1, 2)
        '''

    def test_init_counter(self):
        '''
        init_counter(edge)

        edge = (0, 1)
        '''

    def test_init_counter_error(self):
        '''
        init_counter(edge) -> ValueError

        edge = (-1, 2)
        '''

    def test_get_counter(self):
        '''
        get_counter(reset)

        reset = (0, 255)
        '''

    def test_get_counter_error(self):
        '''
        get_counter(reset) -> ValueError

        reset = (-1, 256)
        '''

    def test_init_capture(self):
        '''
        init_capture(period)

        period = (0, 65535)
        '''

    def test_init_capture_error(self):
        '''
        init_capture(period) -> ValueError

        period = (-1, 65536)
        '''

    def test_get_capture(self):
        '''
        get_capture(mode)

        mode = (0, 1, 2)
        '''

    def test_get_capture_error(self):
        '''
        get_capture(mode) -> ValueError

        mode = (-1, 3)
        '''

    def test_init_encoder(self):
        '''
        init_encoder(resolution)

        resolution = (0, 255)
        '''

    def test_init_encoder_error(self):
        '''
        init_encoder(resolution) -> ValueError

        resolution = (-1, 256)
        '''

    def test_init_pwm(self):
        '''
        init_pwm(duty, period)

        duty = (0, 1023)
        period = (0, 65535)
        '''

    def test_init_pwm_error(self):
        '''
        init_pwm(duty, period) -> ValueError

        duty = (-1, 1024)
        period = (-1, 65536)
        '''

    def test___get_calibration(self):
        '''
        __get_calibration(gain_id)

        gain_id (S) = (0, 16)
        gain_id (M) = (0, 5)
        '''

    def test___get_calibration_error(self):
        '''
        __get_calibration(gain_id) -> ValueError

        gain_id (S) = (-1, 17)
        gain_id (M) = (-1, 6)
        '''

    def test___set_calibration(self):
        '''
        __set_calibration(gain_id, gain, offset)

        gain_id (S) = (0, 16)
        gain_id (M) = (0, 5)
        gain = (0, 65535)
        offset = (-32768, 32767)
        '''

    def test___set_calibration_error(self):
        '''
        __set_calibration(gain_id, gain, offset) -> ValueError

        gain_id (S) = (-1, 17)
        gain_id (M) = (-1, 6)
        gain = (-1, 65536)
        offset = (-32769, 32768)
        '''

    def test_set_cal(self):
        '''
        set_cal(gains, offsets, flag)

        gains = (0, 65535)
        len(gains) (M) = 6
        len(gains) (SE, DE) = 17
        offsets = (-32768, 32767)
        len(offsets) (M) = 6
        len(offsets) (SE, DE) = 17
        flag = (M, SE, DE)
        '''

    def test_set_cal_error(self):
        '''
        set_cal(gains, offsets, flag) -> ValueError, LengthError

        gains = (-1, 65536)
        len(gains) (M) = (5, 7)
        len(gains) (SE, DE) = (16, 18)
        offsets = (-32769, 32768)
        len(offsets) (M) = (5, 7)
        len(offsets) (SE, DE) = (16, 18)
        flag != (M, SE, DE)
        '''

    def test_set_dac_cal(self):
        '''
        set_dac_cal(gain, offset)

        gain = (0, 65535)
        offset = (-32768, 32767)
        '''

    def test_set_dac_cal_error(self):
        '''
        set_dac_cal(gain, offset) -> ValueError

        gain = (-1, 65536)
        offset = (-32769, 32768)
        '''

    def test_conf_channel(self):
        '''
        conf_channel(number, mode, pinput, ninput, gain, nsamples)

        number = (1, 4)
        mode = (0, 5)
        pinput = [1-8]
        ninput (S) = (0, [1-8] and ninput = pinput +- 1 (pair))
        ninput (M) = (0, 5, 6, 7, 8, 25)
        gain (S) = (0, 7)
        gain (M) = (0, 4)
        nsamples = (0, 254)
        '''

    def test_conf_channel_error(self):
        '''
        conf_channel(
            number, mode, pinput, ninput, gain, nsamples) -> ValueError

        number = (0, 5)
        mode = (-1, 6)
        pinput = (0, 9)
        ninput (S) = (-1, 9, [1-8] and ninput != pinput +- 1, [1-8] and
            ninput = pinput +- 1 (not pair))
        ninput (M) = (-1, 1, 4, 9, 24, 26)
        gain (S) = (-1, 8)
        gain (M) = (-1, 5)
        nsamples = (-1, 255)
        '''

    def test_setup_channel(self):
        '''
        setup_channel(number, npoints, continuous)

        number = (1, 4)
        npoints = (0, 65535)
        continuous = (0, 1)
        '''

    def test_setup_channel_error(self):
        '''
        setup_channel(number, npoints, continuous) -> ValueError

        number = (0, 5)
        npoints = (-1, 65536)
        continuous = (-1, 2)
        '''

    def test_destroy_channel(self):
        '''
        destroy_channel(number)

        number = (1, 4)
        '''

    def test_destroy_channel_error(self):
        '''
        destroy_channel(number) -> ValueError

        number = (0, 5)
        '''

    def test_create_stream(self):
        '''
        create_stream(number, period)

        number = (1, 4)
        period = (1, 65535)
        '''

    def test_create_stream_error(self):
        '''
        create_stream(number, period) -> ValueError

        number = (0, 5)
        period = (0, 65536)
        '''

    def test_create_burst(self):
        '''
        create_burst(period)

        period = (100, 65535)
        '''

    def test_create_burst_error(self):
        '''
        create_burst(period) -> ValueError

        period = (99, 65536)
        '''

    def test_create_external(self):
        '''
        create_external(number, edge)

        number = (1, 4)
        edge = (0, 1)
        '''

    def test_create_external_error(self):
        '''
        create_external(number, edge) -> ValueError

        number = (0, 5)
        edge = (-1, 2)
        '''

    def test_load_signal(self):
        '''
        load_signal(data, offset)

        data (S) = (0, 4.095)
        data (M) = (-4.096, 4.095)
        len(data) = (1, 400)
        offset = (-32768, 32767)
        '''

    def test_load_signal_error(self):
        '''
        load_signal(data, offset) -> ValueError, LengthError

        data (S) = (-, 4.096)
        data (M) = (-4.097, 4.096)
        len(data) = (0, 401)
        offset = (-32769, 32768)
        '''

    def test_flush_stream(self):
        '''
        flush_stream(data, channel)

        data = irrelevant
        type(data) = list
        channel = (1, 4)
        '''

    def test_flush_stream_error(self):
        '''
        flush_stream(data, channel) -> ValueError, TypeError

        data = irrelevant
        type(data) != list
        channel = (0, 5)
        '''

    def test_get_stream(self):
        '''
        get_stream(data, channel)

        data = irrelevant
        type(data) = list
        channel = irrelevant
        type(channel) = list
        '''

    def test_get_stream_error(self):
        '''
        get_stream(data, channel) -> TypeError

        data = irrelevant
        type(data) != list
        channel = irrelevant
        type(channel) != list
        '''

    def test_set_id(self):
        '''
        set_id(id)

        id = (0, 999)
        '''

    def test_set_id_error(self):
        '''
        set_id(id) -> ValueError

        id = (-1, 1000)
        '''

    def test_spi_config(self):
        '''
        spi_config(cpol, cpha)

        cpol = (0, 1)
        cpha = (0, 1)
        '''

    def test_spi_config_error(self):
        '''
        spi_config(cpol, cpha) -> ValueError

        cpol = (-1, 2)
        cpha = (-1, 2)
        '''

    def test_spi_setup(self):
        '''
        spi_setup(nbytes, sck, mosi, miso)

        nbytes = (0, 3)
        sck = (1, 6)
        mosi = (1, 6)
        miso = (1, 6)
        '''

    def test_spi_setup_error(self):
        '''
        spi_setup(nbytes, sck, mosi, miso) -> ValueError

        nbytes = (-1, 4)
        sck = (0, 7)
        mosi = (0, 7)
        miso = (0, 7)
        '''

    def test_spi_write(self):
        '''
        spi_write(value, word)

        value = (0, 65535)
        word = (0, 1)
        '''

    def test_spi_write_error(self):
        '''
        spi_write(value, word) -> ValueError

        value = (-1, 65536)
        word = (-1, 2)
        '''
    """
