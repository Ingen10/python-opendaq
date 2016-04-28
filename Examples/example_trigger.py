"""example_trigger.py: creating a stream, using digital trigger on D1 (falling edge) to start experiment"""

from opendaq import *
from opendaq.daq import *
import time

# Connect to the device
dq = DAQ("COM3")  # change for the Serial port in which openDAQ is connected

# Set Analog voltage

dq.set_analog(0.9)

stream1 = dq.create_stream(ANALOG_INPUT, 200,npoints = 20, continuous=False)
stream1.analog_setup(pinput=8,ninput=7, gain=GAIN_S_X1)

#Configure trigger (Digital input D1, value = 0 falling edge)
stream1.trigger_setup(1,0)


dq.start()

print "Waiting for trigger..."

while dq.is_measuring():
    time.sleep(1)
    data1 = stream1.read()
    if data1:
        print "data1", data1

	
dq.stop()
