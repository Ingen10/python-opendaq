Quick start
===========

Import the module and connect to the device::

    $ from opendaq import DAQ 	#import the module
    
    $ daq = DAQ("COM2")	#assign the name daqù to the port 
	
Note that the exact name of the port may be different on your computer. 

It could be something like *"ttyUSB0"* in Linux or *'/dev/tty.SLAB_USBtoUART'* in Mac. Ports are listed in `/dev/` directory in both OS.

Command-Response Mode:
^^^^^^^^^^^^^^^^^^^^^^

You can control the LED turning it off (0), green (1), red (2), or, orange (3):: 

    $ daq.set_led(0) 
    $ daq.set_led(1) 
    $ daq.set_led(2)
    $ daq.set_led(3)

Set an output voltage (CR Mode)::

    $ daq.set_analog(0.91)

Configure an analog input and read back the voltage::

    $ daq.conf_adc(pinput=8,ninput=0,gain=1,nsamples=20)
    $ daq.read_analog()


Stream Mode:
^^^^^^^^^^^^

Create a new Experiment, Stream type, with a 100ms period, discontinuous mode  associated to DataChannel #1::

    $ stream_exp =  daq.create_stream(ANALOG_INPUT, 100)

Configure the experiment to be an analog reading (A8 as SE input, gain x1)::

    $ stream_exp.analog_setup(pinput=8,gain=GAIN_S_X1)

Start the experiment::
        
    $ daq.start()

Keep receiving measured data until ::

    $ measuring = True

    $ while dq.is_measuring():
                
        print "data"  , stream_exp.read()	


