# opendaq-python / opendaq

Main project files.

Go to [openDAQ documentation](https://www.google.com "DAQ.py walkthrough") in ReadTheDocs to take a look at the functions included in them.

* * * 

## Using opendaq-utils script for calibrating openDAQ devices

This script provides useful tools for device testing and analog calibration.

Once the opendaq library has been istalled in the system, the script can be called directly from command promt: `$ opendaq-utils`.
The script needs some arguments and uses sub-commands to control the specific actions to be executed:

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
2. All the analog inputs will be calibrated, as well as the analog output (DAC). The easiest way is to connect all of them in between (all the AIN and the DAC together).
3. Reset the old calibration: `opendaq-utils calib -r`.
4. Apply some different output voltages ( `opendaq-utils set-voltage -i`) and anotate them in a file (`\calib.txt`). They will be used for DAC calibration.
5. Execute full calibration script: `opendaq-utils calib -l`. Using the values from the file, and if the DAC output is correctly connected to all the inputs, the system will calibrate itself.
6. You can execute a test to check the accuracy of the new calibration: `opendaq-utils test -l`

