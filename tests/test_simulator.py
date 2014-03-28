import unittest
from opendaq.common import mkcmd
from opendaq.simulator import DAQSimulator

NAK = mkcmd(160, '')


class TestSimulator(unittest.TestCase):
    def cmd_fail(self, ncmd, fmt, *args):
        """ Assert that a given command will fail """
        cmd = mkcmd(ncmd, fmt, *args)
        self.daq.write(cmd)
        assert self.daq.read(4) == NAK

    def cmd_echo(self, ncmd, fmt, *args):
        """ Assert that a given command will return an echo """
        cmd = mkcmd(ncmd, fmt, *args)
        self.daq.write(cmd)
        assert self.daq.read(len(cmd)) == cmd

    def setUp(self):
        self.daq = DAQSimulator()

    def test_unknown_command(self):
        self.cmd_fail(220, 'B', 1)

    def test_set_led(self):
        self.cmd_echo(18, 'B', 1)
        assert self.daq.led_color == 1

    def test_set_led_error(self):
        # invalid color
        self.cmd_fail(18, 'B', 4)

    def test_set_dac(self):
        self.cmd_echo(13, 'h', -1200)
        assert self.daq.dac_value == -1200

    def test_set_dac_error(self):
        # invalid DAC value
        self.cmd_fail(13, 'h', 5000)
