import serial
import time
from opendaq import *
from opendaq.daq import *
import numpy as np

GAINx05  = 0
GAINx1   = 1
GAINX2   = 2
GAINx10  = 3
GAINx100 = 4

# Connect to the device
dq = DAQ("COM9")  # change for the Serial port in which openDAQ is connected
period1 = 200
numberPoints1 = 20
numberPoints2 = 10
pinput = 8
ninput = 0
nSamples = 20
gain = GAINx05

# ------------------------------------------------------------

preload_buffer = [0.3, 1, 3.3, 2]
stream_source = dq.create_stream(
    200, ANALOG_OUTPUT, continuous=True, npoints=len(preload_buffer))
stream_source.analog_setup()
dq.load_signal(preload_buffer)

# ------------------------------------------------------------

stream1 = dq.create_stream(
    period1, ANALOG_INPUT, continuous=True, npoints=numberPoints1)
stream1.analog_setup(
    pinput=pinput, ninput=ninput, gain=gain, nsamples=nSamples)

dq.start()

while True:
    time.sleep(1)
    measuring = dq.is_measuring()
    data1 = stream1.read()

    print "data1", data1

    if not measuring:
        break
