# opendaq-python

Python binding for openDAQ hardware.

openDAQ libraries and examples are compatible with Python 2.7 and 3.X.

Go to [openDAQ documentation](http://opendaq-python.readthedocs.io/en/latest/)
for complete documentation of the packet.

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

You will need **administrator rights** (root access) to install this package
system-wide.

To install the last stable version:

```sh
    $ pip install opendaq
```

To install the development version (it is highly recommended to use a
[virtual environment](https://virtualenv.pypa.io/en/stable/) for this):

```sh
    $ git clone github.com/opendaq/opendaq-python
    $ cd opendaq-python
    $ python setup.py install
```

## Quick start

### Command-Response Mode:

To start measuring, just import the module and connect to the device:

```sh
    $ from opendaq import * 	#import the module and definitions
    $ daq = DAQ("COM2")         # assign a name to the device instance (daq) and connect to serial port
```

Note that the exact name of the port may be different on your computer.

In Windows, you can go to *System/Device Manager*, in the *Control Panel*, to
check the name of the port that the openDAQ device is using.

The name of the port could be something like `/dev/ttyUSB0` in Linux or
`/dev/tty.SLAB_USBtoUART` in Mac. Ports are listed in `/dev/` directory at both
OS.

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

## Calibration

The `opendaq-utils` script provides useful tools for device testing and analog calibration.

Once the opendaq library has been istalled in the system, the script can be
called directly from command promt:

    $ opendaq-utils

The script needs some arguments and uses sub-commands to control the specific
actions to be executed:

```sh
Usage: opendaq-utils [-h] [-p PORT] [-m METER] (info, calib, serial, test, set-voltage)

Optional arguments:
    -h, --help              show help message
    -p PORT, --port PORT    select serial port (default: /dev/ttyUSB0)
    -m METER, --meter METER Use a digital multimeter for fully automated test

Subcomands:
    info                    Show device information and versions
    calib                   Calibrate the devices
    test                    Test device calibration
    set-voltage             Set DAC voltage
    serial                  Read or write the serial number


[opendaq-utils calib] optional arguments:
    -l, --log               generate log file
    -r, --reset             reset the calibration values
    -d, --dac               Apply only DAC calibration and exit
    -f FILE, --file FILE    Select fiel source to load DAC parameters (default: calib.txt)
    -s, --show              Show calibration values
    -a, --auto              Use the external USB multimeter to perform automated calibration

[opendaq-utils test] optional arguments:
    -l, --log               generate log file
    -a, --auto              Use the external USB multimeter to perform automated calibration

[opendaq-utils set-voltage] optional arguments:
    -i, --interactive       Interactively ask for voltage values

[opendaq-utils serial] optional arguments:
    -w SERIAL, --write SERIAL   Write a new serial number

```
* * *

Please note that for calibrating the device, you should follow these instructions:

1. You will need an external multimeter or any instrument capable of reading voltages.
2. All the analog inputs will be calibrated, as well as the analog output
   (DAC). The easiest way is to connect all of them in between (all the AIN and
   the DAC together).
3. Reset the old calibration: `opendaq-utils calib -r`.
4. Apply some different output voltages (`opendaq-utils set-voltage -i`) and
   anotate them in a file (`calib.txt`). They will be used for DAC calibration.
5. Execute full calibration script: `opendaq-utils calib -l`. Using the values
   from the file, and if the DAC output is correctly connected to all the
   inputs, the system will calibrate itself.
6. You can execute a test to check the accuracy of the new calibration:

    opendaq-utils test -l
