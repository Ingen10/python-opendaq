Quick start
===========

Import the module and connect to the device::

    $ import opendaq	#import the module
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

    $ daq.conf_adc(8,0,1,20)
    $ daq.read_analog()


Stream Mode:
^^^^^^^^^^^^

Create a new Experiment, Stream type, with a 100ms period, associated to DataChannel #1::

    $ daq.create_stream(1, 100)

Configure the experiment to be an analog reading (A8 as SE input, gain x1)::

    $ daq.conf_channel(1, 0, 8, 0, 1)


Set up the experiment to run continuously::

    $ daq.setup_channel(1, 0)

Create empty arrays to store the data and channel values, and start the experiment::

    $ data = []
    $ chn = []
    $ daq.start()

Keep receiving measured data until you want to stop it::

    $ daq.get_stream(data,chn)
	
The data points will be stored in the `data` array, while `chn` array will store the experiment id of each point. 
Note that data points are returned as a raw digital value from this function. You will have to externally apply the calibration of the device to get the actual voltages.