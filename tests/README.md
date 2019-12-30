Tests usage
-----------

Each of these tests evaluate different aspects of the code. In order to
execute this tests, go to the parent directory, and run the following:


```sh

$ make test

```

Note:  Some of the hardware tests (test_daq_hw.py file) require connections to
be made in the device.

 - Connect DAC to AN8 and GND to AN7
 - Configure the appropiate serial port

If you do not have a physical device connected to the PC, disable that test.
