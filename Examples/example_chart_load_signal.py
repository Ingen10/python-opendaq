""" Plotting a chart from a stream type experiment, and use another experiment to generate the signal """

import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
from opendaq.daq import *
import time

#Change to the serial port in wich openDAQ is actually connected
dq = DAQ("COM3")

#Configure the first experiment, the one that will be plotted
data_rate = 20
stream1 = dq.create_stream(ANALOG_INPUT, data_rate,continuous=True)
stream1.analog_setup(pinput=8, gain=GAIN_S_X1)

#Configure the second experiment, a custom signal generated from a stream
preload_buffer = [ -2.5, -1, 0, 1, 2.5]
stream2 = dq.create_stream(ANALOG_OUTPUT, period=500, npoints=len(preload_buffer),continuous=True)
stream2.load_signal(preload_buffer,clear=True)

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
        a = stream1.read()
        l = len(a)
        data.extend(a) #append values list with new points from the stream
        t.extend([t0+(data_rate*x)/1000.0 for x in range (l)])  #append time list with the same number of elements
        t0 += (l*data_rate)/1000.0  #increase the time reference
        plt.plot(t, data,color="blue",linewidth=1.5, linestyle="-")
        plt.draw()
    except KeyboardInterrupt:
        break
#stop the experiment
dq.stop()


