""" Create an stream and plottin the data"""

import serial
import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
from opendaq import DAQ
from opendaq.daq import *
import time

#Change for the serial port in wich openDAQ is connected
dq = DAQ("COM3")

dq.set_analog(1)

data_rate = 200
stream = dq.create_stream(ANALOG_INPUT, data_rate,continuous=True)
stream.analog_setup(pinput=8, gain=GAIN_S_X1)

t0 = 0.0
t =[]
data = []

dq.start()

fig = plt.figure()
plt.ion()
plt.show()

while dq.measuring:
    try:
        time.sleep(1)
        a = stream.read()
        l = len(a)
        data.extend(a)
        t.extend([t0+(data_rate*x)/1000.0 for x in range (l)])
        t0 += (l*data_rate)/1000.0
        plt.plot(t, data,color="blue",linewidth=2.5, linestyle="-")
        plt.draw()
    except KeyboardInterrupt:
        break

dq.stop()


