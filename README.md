# opendaq-python

Python binding for openDAQ hardware.

openDAQ libraries and examples are compatible with Python 2.7 and 3.X.

Go to [openDAQ documentation](http://opendaq-python.readthedocs.io/en/latest/ "DAQ.py walkthrough") in *ReadTheDocs* for complete documentation of the library.

* * *

OpenDAQ is an open source data acquisition instrument, which provides user with
several physical interaction capabilities such as analog inputs and outputs,
digital inputs and outputs, timers and counters.

By means of an USB connection, openDAQ brings all the information that it
captures to a host computer, where you can decide how to process, display and
store it. Several demos and examples are provided in website's support page.
(http://www.open-daq.com/paginas/support)

Please, go to http://www.open-daq.com for additional info.
For support, e-mail to support@open-daq.com

* * * 

## Installation

You will need **administrator rights** (root access) to install this package system-wide.

It is possible to install the package using **pip**:

```sh
    $ pip install opendaq
```

If you dont have pip, then use the console and go to the folder where you downloaded the opendaq-python package:

```sh
    $ python setup.py install
```

To start measuring, just import the module and connect to the device:

```sh
    $ from opendaq import DAQ, ExpMode, Gains, LedColor 	#import the module and definitions
    $ daq = DAQ("COM2")	# assign a name to the device instance (daq) and connect to serial port
```

Note that the exact name of the port may be different on your computer. 

In Windows, you can go to *System/Device Manager*, in the *Control Panel*, to check the name of the port that the openDAQ device is using.

The name of the port could be something like `/dev/ttyUSB0` in Linux or `/dev/tty.SLAB_USBtoUART` in Mac. Ports are listed in `/dev/` directory at both OS.

    
## Quick start    

### Command-Response Mode:

You can control the LED turning it off, green, red or orange:

```python
    daq.set_led(LedColor.RED)
```

Set an output voltage (CR Mode):

```python
    daq.set_analog(0.91)
```

Configure an analog input and read the voltage:

```python
    daq.conf_adc(pinput=8, ninput=0, gain=Gains.M.x1)
    daq.read_analog()
```

### Stream Mode:

Create a new Experiment, Stream type, analog input mode, with a 100 milliseconds period, not-continuous
mode, 30 total points. Then, configure that experiment to read from A8 as SE input, gain 1x):


```python
    stream_exp = daq.create_stream(ExpMode.ANALOG_IN, 100, 30, continuous=False)
    stream_exp.analog_setup(pinput=8, gain=Gains.M.x1)
```

Start the experiment and keep receiving measured data until it has ended reading all the points:

```python
    daq.start()
    while daq.is_measuring:
    	print "data=", stream_exp.read()
```

Go to **[openDAQ documentation](http://opendaq-python.readthedocs.io/en/latest/ "DAQ.py walkthrough")** in *ReadTheDocs* to read more information about the library.

There are some basic example scripts included in this repository (see */examples* folder) to help you 
understanding the syntaxis.


## Development

You will need some additional development tools if you want to collaborate with this project.
They can be installed at once using pip:
```sh
    $ pip install -r requirements-dev.txt
```
You can also install the package in `development` mode:
```sh
    $ python setup.py develop
```



