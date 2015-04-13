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
period1 = 200
numberPoints1 = 30
pinput = 8
ninput = 0
nSamples = 20
gain = GAINx05

# ------------------------------------------------------------

preload_buffer = [0.3, 1, 3.3, 2]
stream_source = dq.create_stream()
stream_source.setup(200, len(preload_buffer), 1, 0, 0, 0, 0, False)
dq.load_signal(preload_buffer)

# ------------------------------------------------------------

stream1 = dq.create_stream()
stream1.setup(period1, numberPoints1, 0, pinput, ninput, gain, nSamples)

dq.start()

while True:
    time.sleep(1)
    measuring = dq.is_measuring()
    data1 = stream1.read()

    print "data1", data1

    if not measuring:
        break
