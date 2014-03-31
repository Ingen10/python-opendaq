import unittest
from opendaq import DAQ


class TestDAQ(unittest.TestCase):
    def setUp(self):
        self.daq = DAQ('sim')
        self.sim = self.daq.ser

    def tearDown(self):
        self.daq.close()

    def test_set_led(self):
        for color in range(4):
            self.daq.set_led(color)
            assert self.sim.led_color == color

    def test_set_led_error(self):
        # invalid color
        self.assertRaises(ValueError, self.daq.set_led, 4)
        self.assertRaises(ValueError, self.daq.set_led, -1)

    def test_get_info(self):
        hw_ver, fw_ver, dev_id = self.daq.get_info()
        assert hw_ver == self.sim.hw_ver
        assert fw_ver == self.sim.fw_ver
        assert dev_id == self.sim.dev_id

    def test_pio(self):
        for pio in range(6):
            self.daq.set_pio(pio + 1, 1)
            assert self.sim.pios[pio] == 1
            self.daq.set_pio(pio + 1, 0)
            assert self.sim.pios[pio] == 0

    def test_pio_dir(self):
        for pio in range(6):
            self.daq.set_pio_dir(pio + 1, 1)
            assert self.sim.pios_dir[pio] == 1
            self.daq.set_pio_dir(pio + 1, 0)
            assert self.sim.pios_dir[pio] == 0
