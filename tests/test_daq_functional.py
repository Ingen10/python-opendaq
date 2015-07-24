import unittest
from opendaq import DAQ

'''
connections to make tests:
    A8 - DAQ
    A7 - AGND
    D5 - D6

'''

class TestDAQFunctional(unittest.TestCase):
    def test_init(self):
        '''
        test hw_ver, port, measuring...
        '''

    def test_open(self):
        '''
        test port is open
        '''

    def test_close(self):
        '''
        close()
        test port is closed
        open() or put this test at the end
        '''

    def test_get_info(self):
        '''
        test get_info() returns the right hardware model
        '''

    def test_set_read_analog(self):
        '''
        set_analog(value)
        conf_adc(8)
        test read_analog() returns value
        conf_adc(8, 7)
        test read_analog() returns value
        conf_adc(8, 7, gain, samples)
        test read_analog() returns value
        '''

    def test_conf_adc(self):
        '''
        conf_adc(pinput, ninput, gain)

        test daq.gain = gain
        test daq.pinput:
            daq.pinput == pinput if:
                model == M
                model == S and ninput == 0
            if model == S and ninput != 0:
                ninput = 9 if inputs == (1,2) or (2,1)
                ...
                ninput = 12 if inputs == (7,8) or (8,7)
        '''

    def test_volts_to_raw(self):
        '''
        test __volts_to_raw(volts) returns the right raw value
        '''

    def test_pio(self):
        '''
        set_port_dir(x) -> 5 input 6 output
        set_port(x) -> put high in 6
        test input 5 is high (set_port)
        set_port(x) -> put low in 6
        test input 5 is low (set_port)

        set_pio_dir() -> 5 output 6 input
        set_pio -> put high in 5
        test input 6 is high (set_port)
        set_pio -> put low in 5
        test input 6 is low (set_port)
        '''

    def test_counter(self):
        '''
        init_counter(1) -> initializes counter high
        set_pio -> put low-high-...-low-high in 6
        test get_counter(1) counts right

        init_counter(0)
        set_pio -> put high-low-...-high-low in 6
        test get_counter(0) counts right
        '''

    def test_capture(self):
        '''
        test init_capture(period) returns period
        stop_capture()
        '''

    def test_encoder(self):
        '''
        test init_encoder(resolution) returns resolution
        stop_encoder()
        '''

    def test_pwm(self):
        '''
        test init_pwm(duty, period) returns duty, period
        stop_pwm()
        '''

    def test_calibration(self):
        '''
        make calibration backup
        
        set_daq_cal(gain, offset)
        set_cal(gains, offsets)
        test get_daq_cal() returns gain and offset
        test get_cal() returns gains and offsets

        restore calibration backup
        '''

    def test_channel(self):
        '''
        test conf_channel(number, mode, pinput, ninput, gain, nsamples) return
        test setup_channel(number, npoints, continuous) return
        test destroy_channel(number) return
        '''

    def test_stream(self):
        '''
        test create_stream(number, period) returns number, period
        test create_burst(period) returns period
        test create_external(number, edge) returns number, edge
        test get_stream([], []) returns 0
        '''

    def test_measure(self):
        '''
        test measuring == False
        start()
        test measuring == True
        stop()
        test measuring == False
        '''

    def test_id(self):
        '''
        make id bakup (get_info())
        
        set_id(id)
        test get_info() returns right id

        restore id backup
        '''

    def test_spi(self):
        '''
        test spi_config(cpol, cpha) returns cpol, cpha
        test spi_setup(nbytes, sck, mosi, miso) returns sck, mosi, miso
        test spi_write(value, word) returns value
        '''