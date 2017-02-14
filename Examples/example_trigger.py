"""Creating a stream, using digital trigger on D1
(falling edge) to start the experiment"""

import time
from opendaq import DAQ, ExpMode, Gains

# Connect to the device
dq = DAQ('/dev/ttyUSB0')

# Set Analog voltage
dq.set_analog(0.9)

stream1 = dq.create_stream(ExpMode.ANALOG_IN, 200, npoints=20,
                           continuous=False)
stream1.analog_setup(pinput=8, ninput=7, gain=Gains.S.x1)

# Configure trigger (Digital input D1, value = 0 falling edge)
stream1.trigger_setup(1, 0)

dq.start()

print "Waiting for trigger..."

while dq.is_measuring:
    time.sleep(1)
    data1 = stream1.read()
    if data1:
        print "data1", data1

dq.stop()
