import unittest
from opendaq import DAQ
import struct
from opendaq import *
from opendaq.daq import *

"""
Script for testing against the hardware

"""

class TestDAQHW(unittest.TestCase):
    def setUp(self):
        self.daq = DAQ('/dev/ttyUSB0')
        
    def tearDown(self):
        self.daq.close()

    def test_set_ledhw(self):
        for color in range(4):
            self.daq.set_led(color)
            cmd = struct.pack('!BBB', 18, 1, color)
            assert self.daq.send_command(cmd,'B')[0] == color

    def test_set_led_error_hw(self):
        self.assertRaises(ValueError, self.daq.set_led,4)
        self.assertRaises(ValueError, self.daq.set_led,-1)

    def test_calibration(self):
        # Connect DAC to AN8 and GND to AN7
        self.daq.set_analog(1)
        self.daq.conf_adc(8,0,1,20)
        data = self.daq.read_analog()
        assert data > 0.96
        assert data < 1.04

    def disabled_test_create_stream(self):
        stream = self.daq.create_stream(ANALOG_INPUT, 200, 1, continuous=False)
        stream.analog_setup(pinput=8, gain=GAIN_S_X1)
        self.daq.start()
        measuring = True
        while self.daq.is_measuring():
            mode = stream.get_mode()
            assert mode == ANALOG_INPUT
        

            



    
        


