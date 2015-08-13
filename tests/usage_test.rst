Tests
-------

There are several test files. Each of these tests evaluate different aspects of the openDAQ features. In order to execute this tests, being in the Makefile directory, run the following:

 .. code:: python
  make tests

Note:  Some of the hardware tests (test_daq_hw.py file) require  connections be made in the device. 
"test_daq_hw.py" tests needs a physical device and some connections to be made on it:
* Connect DAC to AN8 and GND to AN7
* Configure the appropiate serial port
If you do not have a device, disable that test.
