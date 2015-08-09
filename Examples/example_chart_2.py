""" Drawing a simple chart in stream mode"""

import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
from opendaq.daq import *
import time

#Change to the serial port in wich openDAQ is actually connected
dq = DAQ("COM3")

dq.set_analog(1) #set a fix voltage

#Configure the experiment
data_rate = 200
stream = dq.create_stream(ANALOG_INPUT, data_rate,continuous=True)
stream.analog_setup(pinput=7, gain=GAIN_S_X1)

#Initiate lists and variables
t0 = 0.0
t =[]
data = []

#Initiate the plot
fig = plt.figure()
plt.ion()
plt.show()

#start the experiment
dq.start()

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
#stop the experiment
dq.stop()


