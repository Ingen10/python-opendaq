Quick start
===========

Import the module and connect to the device::

    $ from opendaq import DAQ 	#import the module
    
    $ daq = DAQ("COM2")	#assign a name to the device instance (daq) 
	
Note that the exact name of the port may be different on your computer. 

It could be something like *"ttyUSB0"* in Linux or *'/dev/tty.SLAB_USBtoUART'* in Mac. Ports are listed in `/dev/` directory at both OS.

Command-Response Mode:
^^^^^^^^^^^^^^^^^^^^^^

You can control the LED turning it off (0), green (1), red (2), or, orange (3):: 

    $ daq.set_led(3)

Set an output voltage (CR Mode)::

    $ daq.set_analog(0.91)

Configure an analog input and read back the voltage::

    $ daq.conf_adc(pinput=8,ninput=0,gain=1,nsamples=20)
    $ daq.read_analog()


Stream Mode:
^^^^^^^^^^^^

Create a new Experiment, Stream type, with a 100ms period, not-continuous mode::

    $ stream_exp =  daq.create_stream(ANALOG_INPUT, 100, npoints=30)

Configure the experiment to read from A8 as SE input, gain x1)::

    $ stream_exp.analog_setup(pinput=8, gain=GAIN_S_X1)

Start the experiments::
        
    $ daq.start()

Keep receiving measured data until it has ended reading all the points::

    $ measuring = True

    $ while dq.is_measuring():
                
    $ 		print "data=", stream_exp.read()	


** See usage.rst to read documentation about the library. **
** There are some helpful examples in this repository to help you understanding the syntaxis. **


