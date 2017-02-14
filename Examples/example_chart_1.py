"""Drawing a real-time chart using command-response mode"""

from time import sleep
import matplotlib.pyplot as plt
from opendaq import DAQ

# Change  to the serial port in which openDAQ is actually connected
dq = DAQ('COM3')
dq.conf_adc(8)  # Reading in AN8
dq.read_adc()

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
        dq.set_analog(i/50.0 + .5)  # we will plot a ramp line

        data.append(dq.read_analog())   # add a new point to the plot
        t.append(period*i)     # update time list

        print(i, data[i])

        plt.plot(t, data, color="blue", linewidth=2.5, linestyle="-")
        plt.draw()
        sleep(period)    # wait for next point
    except KeyboardInterrupt:
        break

plt.close()
dq.close()
