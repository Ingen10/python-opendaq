""" Create an stream and plottin the data"""

import serial
import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
from opendaq import DAQ
from opendaq.daq import *
import time

dq = DAQ("/dev/ttyUSB0")#Change for the serial port in wich openDAQ is connected
dq.set_analog(1)

stream = dq.create_stream(ANALOG_INPUT, 200, 1, continuous=True)
stream.analog_setup(pinput=8, gain=GAIN_S_X1)
t =[]
data = []
dq.start()
delta_t = 0.5
for i in range (0, 49):
    try:
        time.sleep(delta_t)
        data.append( stream.read()[0] )
        print data[i]
        data.append(data[i])
        t.append(delta_t*i)
    except KeyboardInterrupt:
        break
    

dq.stop()
print len(data)
print len(t)
print data
plt.plot(t,data)
plt.show()


