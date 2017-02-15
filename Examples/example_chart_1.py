"""Drawing a real-time chart using command-response mode"""

import os
from time import sleep
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
fig = plt.figure()
plt.ion()
plt.show()

# initiate lists
t = []
data = []

for i in range(50):
    try:
        daq.set_analog(i/50.0 + .5)  # we will plot a ramp line

        data.append(daq.read_analog())   # add a new point to the plot
        t.append(period*i)     # update time list

        print(i, data[i])

        plt.plot(t, data, color="blue", linewidth=2.5, linestyle="-")
        plt.draw()
        sleep(period)    # wait for next point
    except KeyboardInterrupt:
        break

plt.close()
daq.close()
