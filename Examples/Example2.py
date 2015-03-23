import serial
import time
import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
import numpy as np

GAINx05  = 0
GAINx1   = 1
GAINX2   = 2
GAINx10  = 3
GAINx100 = 4 

#Connect to the device 
dq = DAQ("COM9") 	#change for the Serial port in which your device is connected
period1 = 200
numberPoints1 = 14
period2 = 300
numberPoints2 = 11
period3 = 170
numberPoints3 = 3
pinput = 8
ninput = 0
nSamples = 20
gain = GAINx05

dq.set_analog(0.9)

#------------------------------------------------------------


stream1 = dq.create_stream(1)
stream1.setup(period1, numberPoints1, 1)
stream1.analog_setup(0, pinput, ninput, gain, nSamples)

stream2 = dq.create_stream(2)
stream2.setup(period2, numberPoints2, 1)
stream2.analog_setup(0, pinput, ninput, gain, nSamples)

"""
stream3 = dq.create_stream(3)
stream3.setup(period3, numberPoints3, 1)
stream3.analog_setup(0, pinput, ninput, gain, nSamples)
"""

dq.start()

while True:
    time.sleep(1)
    measuring = dq.is_measuring()
    data1 = stream1.read()
    data2 = stream2.read()
    #data3 = stream2.read()

    print "data1", data1
    print "data2", data2
    #print "data3", data3
    if not measuring:
        break


"""
stream1 = dq.create_stream(1)
stream1.setup(period1, numberPoints1, 1)
stream1.analog_setup(0, pinput, ninput, gain, nSamples)
dq.start()

data1 = stream1.read()
print "data1", data1

data1 = stream1.read()
print "data1", data1
"""
