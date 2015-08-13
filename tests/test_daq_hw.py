import unittest
# import struct
from opendaq import *
from opendaq.daq import *

"""
Script for testing against the hardware
This tests needs a physical device and some connections to be made on it:
* Connect DAC to AN8 and GND to AN7

"""


class TestDAQHW(unittest.TestCase):
    def setUp(self):
        self.daq = DAQ("COM3")

    def tearDown(self):
        self.daq.close()

    def test_set_ledhw(self):
        for color in range(4):
            assert color == self.daq.set_led(color)

    def test_set_led_error_hw(self):
        self.assertRaises(ValueError, self.daq.set_led, 4)
        self.assertRaises(ValueError, self.daq.set_led, -1)

    def test_calibration(self):
        # Connect DAC to AN8 and GND to AN7
        self.daq.set_analog(1)
        self.daq.conf_adc(8, 0, 1, 20)
        data = self.daq.read_analog()
        assert data > 0.9
        assert data < 1.1

    def disabled_test_create_stream(self):
        stream = self.daq.create_stream(ANALOG_INPUT, 200, 1, continuous=False)
        stream.analog_setup(pinput=8, gain=GAIN_S_X1)
        self.daq.start()
        while self.daq.is_measuring():
            mode = stream.get_mode()
            assert mode == ANALOG_INPUT
