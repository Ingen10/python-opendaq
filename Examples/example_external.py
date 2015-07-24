""" Configure an external experiment."""


from opendaq import *
from opendaq.daq import *
import time

# Connect to the device
dq = DAQ("COM3")  # change for the Serial port in which openDAQ is connected

# Set Analog voltage
dq.set_analog(0.9)

external1 = dq.create_external(ANALOG_INPUT, 1, edge=1, npoints=10, continuous=False, buffersize=1000)
external1.analog_setup(pinput=8, ninput=0, gain=GAIN_S_X1, nsamples=20)

dq.start()
while dq.is_measuring():
    time.sleep(1)
    print "data1", external1.read()
