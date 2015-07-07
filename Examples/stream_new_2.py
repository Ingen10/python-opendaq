from opendaq import *
from opendaq.daq import *
import time
import sys

# Connect to the device
dq = DAQ("COM9")  # change for the Serial port in which openDAQ is connected

# Set Analog voltage
dq.set_analog(0.9)

stream1 = dq.create_stream(ANALOG_INPUT, 200, continuous=True)
stream1.analog_setup(pinput=8, gain=GAIN_S_X1)

stream2 = dq.create_stream(ANALOG_INPUT, 300, continuous=True)
stream2.analog_setup(pinput=8, ninput=7, gain=GAIN_S_X2)

dq.start()
measuring = True
while measuring:
    measuring =  dq.is_measuring()
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print "capturando interrupcion"
        measuring = False
        break
        print "fin captura"
    print "data1", stream1.read()
    print "data2", stream2.read()
    
