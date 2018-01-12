"""Drawing a simple chart in stream mode"""

import os
import time
import matplotlib.pyplot as plt
from opendaq import DAQ, ExpMode, Gains

# Change here the serial port in which the openDAQ is connected
port = '/dev/ttyUSB0' if os.name == 'posix' else 'COM3'

# Connect to the device
daq = DAQ(port)

daq.set_analog(1)    # set a fix voltage

# Configure the experiment
data_rate = 200
stream = daq.create_stream(ExpMode.ANALOG_IN, data_rate, continuous=True)
stream.analog_setup(pinput=8, gain=Gains.S.x1)

# Initiate lists and variables
t0 = 0.0
t = []
data = []

# Initiate the plot
fig = plt.figure()
plt.ion()
plt.show()

# start the experiment
daq.start()

while daq.is_measuring:
    try:
        time.sleep(1)
        a = stream.read()
        l = len(a)
        data.extend(a)
        t.extend([t0+(data_rate*x)/1000.0 for x in range(l)])
        t0 += (l*data_rate)/1000.0
        plt.plot(t, data, color="blue", linewidth=2.5, linestyle="-")
        plt.draw()
    except KeyboardInterrupt:
        plt.close()
        # stop the experiment
        daq.stop()
        daq.close()
        break
