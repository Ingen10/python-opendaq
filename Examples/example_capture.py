from __future__ import print_function
from opendaq import *
import time

# Connect to the device
# change for the Serial port in which openDAQ is connected
daq = DAQ('COM3')

daq.init_capture(12500)

for i in range(20):
    try:
        time.sleep(1)
        a = daq.get_capture(2)   # 2: full period
        print("T: ", 1000. / a[1])
    except KeyboardInterrupt:
        daq.close()

daq.stop()
