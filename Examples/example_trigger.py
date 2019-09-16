"""Creating a stream, using digital trigger on D1
(falling edge) to start the experiment"""
from __future__ import print_function
import time
import os
from opendaq import DAQ, ExpMode, Trigger

# Change here the serial port in which the openDAQ is connected
port = '/dev/ttyUSB0' if os.name == 'posix' else 'COM3'

# Connect to the device
daq = DAQ(port)

# Set Analog voltage
daq.set_analog(0.9)

stream1 = daq.create_stream(ExpMode.ANALOG_IN, 200, npoints=20,
                           continuous=False)
stream1.analog_setup(pinput=8, ninput=7, gain='x1')

# Configure trigger (Digital input D1, value = 0 falling edge)
stream1.trigger_setup(Trigger.DIN1, 0)

daq.start()

print("Waiting for trigger...")

while daq.is_measuring:
    time.sleep(1)
    data1 = stream1.read()
    if data1:
        print("data1", data1)

daq.stop()
