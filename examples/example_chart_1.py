"""Drawing a real-time chart using command-response mode"""

import os
import time
from time import sleep
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from opendaq import DAQ

# Change here the serial port in which the openDAQ is connected
port = '/dev/ttyUSB0' if os.name == 'posix' else 'COM3'

# Connect to the device
daq = DAQ(port)

daq.conf_adc(8)  # Reading in AN8
daq.read_adc()

period = 0.05

# Initiate plot:
plt.ioff()

# initiate lists
t = []
data = []

for i in range(50):
    try:
        daq.set_analog(i/50.0 + .5)  # we will plot a ramp line

        data.append(daq.read_analog())   # add a new point to the plot
        t.append(period*i)     # update time list

        print(i, data[i])
        sleep(period)    # wait for next point
    except KeyboardInterrupt:
        plt.close()
        daq.close()
        break
plt.plot(t, data, color="blue", linewidth=2.5, linestyle="-")
plt.show()
plt.close()
daq.close()
