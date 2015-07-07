import serial
import time
from opendaq import *
import numpy as np

GAINx05  = 0
GAINx1   = 1
GAINX2   = 2
GAINx10  = 3
GAINx100 = 4

# Connect to the device
dq = DAQ("COM9")  # change for the Serial port in which openDAQ is connected
numberPoints1 = 10
pinput = 8
ninput = 0
nSamples = 20
gain = GAINx05

dq.set_analog(0.9)

# ------------------------------------------------------------

external1 = dq.create_external()
external1.setup(1, numberPoints1, 0, pinput, ninput, gain, nSamples)

dq.start()

while True:
    time.sleep(1)
    measuring = dq.is_measuring()
    data1 = external1.read()

    print "data1", data1

    if not measuring:
        break
