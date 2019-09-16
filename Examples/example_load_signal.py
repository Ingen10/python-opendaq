"""Basic configuration for loading a signal,
generate it through the analog output"""

from __future__ import print_function
import os
import time
from opendaq import DAQ, ExpMode

# Change here the serial port in which the openDAQ is connected
port = '/dev/ttyUSB0' if os.name == 'posix' else 'COM3'

# Connect to the device
daq = DAQ(port)

# create a ramp signal with 4 samples
signal = list(range(4))

stream1 = daq.create_stream(ExpMode.ANALOG_IN, 300, npoints=len(signal))
stream1.analog_setup(pinput=8, gain='x1')

stream2 = daq.create_stream(ExpMode.ANALOG_OUT, 300, npoints=len(signal))
stream2.load_signal(signal)

daq.start()

while daq.is_measuring:
    time.sleep(1)

print("data1", stream1.read())

daq.stop()
