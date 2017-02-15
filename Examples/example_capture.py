from __future__ import print_function
import os
import time
from opendaq import *

# Change here the serial port in which the openDAQ is connected
port = '/dev/ttyUSB0' if os.name == 'posix' else 'COM3'

# Connect to the device
daq = DAQ(port)


daq.init_capture(12500)

for i in range(20):
    try:
        time.sleep(1)
        a = daq.get_capture(2)   # 2: full period
        print("T: ", 1000. / a[1])
    except KeyboardInterrupt:
        daq.close()

daq.stop()
