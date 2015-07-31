"""Plotting in real time """

import serial
import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
from opendaq import DAQ
import time

dq = DAQ("COM3") #Change  for the serial port in which openDAQ is connected 
dq.set_analog(1)
dq.conf_adc(8)#Reading in AN8

fig = plt.figure()
plt.ion()
plt.show()
t = [0]
data = []
i = 0
while True:
    try: 
        data.append(dq.read_analog())
        plt.plot(t, data,color="blue",linewidth=2.5, linestyle="-")
        plt.draw()
        time.sleep(0.5)
        t.append(t[i]+ 0.5)
        i = i+1
    except KeyboardInterrupt:
        break
