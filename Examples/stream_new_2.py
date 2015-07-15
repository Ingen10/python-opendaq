from opendaq import *
from opendaq.daq import *
import time

# Connect to the device
dq = DAQ("COM9", True)  # change for the Serial port in which openDAQ is connected

# Set Analog voltage
dq.set_analog(0.9)

stream1 = dq.create_stream(ANALOG_INPUT, 200, continuous=False)
stream1.analog_setup(pinput=8, gain=GAIN_S_X1)

stream2 = dq.create_stream(ANALOG_INPUT, 300, continuous=False)
stream2.analog_setup(pinput=8, ninput=7, gain=GAIN_S_X2)

dq.start()
measuring = True
while dq.is_measuring():
    time.sleep(1)
    print "data1", stream1.read()
    print "data2", stream2.read()
    
