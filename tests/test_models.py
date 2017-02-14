import unittest
from opendaq.models import DAQModel, Gains, ModelM
from opendaq.daq_model import CalibReg


class TestModelM(unittest.TestCase):
    def test_gains(self):
        assert Gains.M.x033 == 0
        assert Gains.M.x1 == 1
        assert Gains.M.x100 == 4
        assert Gains.M.values == [1./3, 1, 2, 10, 100]

    def test_create(self):
        m = ModelM(140, 123)
        assert m.model_str == '[M]'
        assert m.fw_ver == 140
        assert m.serial_str == 'ODM081237'
        assert m.npios == 6
        assert m.nleds == 1
        assert m.adc.vmin == -4.096
        assert m.dac.vmin == -4.096

    def test_adc_slots(self):
        m = ModelM(140, 123)
        assert m._get_adc_slots(0, 1, 0) == (0, 8)
        assert m._get_adc_slots(0, 2, 0) == (1, 8)
        assert m._get_adc_slots(1, 1, 0) == (0, 9)
        assert m._get_adc_slots(1, 2, 1) == (1, 9)

    def test_factory(self):
        m = DAQModel.new(1, 140, 123)
        assert m.model_str == '[M]'

    def test_raw_to_volts(self):
        m = ModelM(140, 123)
        assert m.raw_to_volts(0, 0, 1, 0) == 0
        assert m.raw_to_volts(32768, 0, 1, 0) == 4.096*3
        assert m.raw_to_volts(-32768, 0, 1, 0) == -4.096*3
        assert m.raw_to_volts(32768, 1, 1, 0) == 4.096
        assert m.raw_to_volts(-32768, 1, 1, 0) == -4.096

    def test_adc_calib(self):
        m = ModelM(140, 123)

        m.adc_calib[0] = CalibReg(1.0, 80)
        m.adc_calib[9] = CalibReg(1.0, 80)
        assert m.raw_to_volts(0, 1, 1, 0) == -0.02

        m.adc_calib[0] = CalibReg(1.1, 0)
        m.adc_calib[9] = CalibReg(1.1, 0)
        out = 8000*(4.096/32768)/1.1/1.1
        assert abs(m.raw_to_volts(8000, 1, 1, 0) - out) < 1e-8

    def test_dac_calib(self):
        m = ModelM(140, 123)

        m.dac_calib[0] = CalibReg(1.0, -0.1)
        assert m.volts_to_raw(0, 0) == 800

    def test_volts_to_raw(self):
        m = ModelM(140, 123)
        assert m.volts_to_raw(0, 0) == 0
        assert m.volts_to_raw(4.096, 0) == 32767
        assert m.volts_to_raw(-4.096, 0) == -32768

        self.assertRaises(ValueError, m.volts_to_raw, 5, 0)
        self.assertRaises(IndexError, m.volts_to_raw, 0, 1)
