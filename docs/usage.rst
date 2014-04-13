============================================
Usage of the opendaq-python package (daq.py)
============================================

Device connection and port handling
-----------------------------------

    DAQ(port, debug=False)
    
    close()
    

ADC reading (CR mode)
---------------------
    conf_adc(pinput, ninput=0, gain=0, nsamples=20)
    
    read_analog()
    
    read_adc()
    

DAC setting (CR mode)
---------------------
    set_analog(volts)
    
    set_dac(raw)
    

Stream Experiments Creation (Stream Mode)
-----------------------------------------
    create_burst(period) 
    
    create_external(number, edge) 
    
    create_stream(number, period)
    
    destroy_channel(number)
    

DataChannel Configuration (Stream Mode)
----------------------------------------------
    setup_channel(number, npoints, continuous=True)
    
    conf_channel(number, mode, pinput=1, ninput=0, gain=1, nsamples=1)
    
    load_signal(data, offset)
    

Stream Experiments Managing (Stream Mode)
-----------------------------------------
    start()
    
    stop()
    
    flush_stream(data, channel)
    
    get_stream(data, channel, callback=0)


Capture
-------
    init_capture(period)
    
    get_capture(mode)
    
    stop_capture()
    
Counter
-------
    init_counter(edge)
    
    get_counter(reset)

Encoder
-------
    init_encoder(resolution)
    
    get_encoder()
    
    stop_encoder()

PWM
------------------
    init_pwm(duty, period)
    
    stop_pwm()

PIO Configuration and control (CR mode)
---------------------------------------
Single PIO
^^^^^^^^^^
    set_pio(number, value)
    
    set_pio_dir(number, output)    

Full Port
^^^^^^^^^
    set_port(value)
    
    set_port_dir(output)

Bit-Bang SPI
------------
    spi_config(cpol, cpha)
    
    spi_setup(nbytes, sck=1, mosi=2, miso=3)
    
    spi_write(value, word=False)

Other
-----
    enable_crc(on)
    
    get_info()
    
    set_id(id)
    
    set_led(color)


Calibration
-----------
    get_cal()
    
    get_dac_cal()
    
    set_cal(gains, offsets, flag)
    
    set_dac_cal(gain, offset)


