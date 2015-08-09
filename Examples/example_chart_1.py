"""Drawing a simple chart using command-response mode"""

import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
import time

dq = DAQ("COM3") #Change  to the serial port in which openDAQ is actually connected 
dq.conf_adc(7)#Reading in AN7

delaytime = 0.5

#Initiate plot:
fig = plt.figure()
plt.ion()
plt.show()

#initiate lists
t = [0]
data = []
i = 0

while True:
    try: 
        dq.set_analog(i/100.0) #We will plot a ramp line
        data.append(dq.read_analog())   #Add a new point to the plot
        plt.plot(t, data,color="blue",linewidth=2.5, linestyle="-")
        plt.draw()
        time.sleep(delaytime) #wait for next point
        t.append(t[i]+ delaytime) #increment time counter
        i = i+1
    except KeyboardInterrupt:
        break
