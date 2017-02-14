"""Create two streams, halt them and restart them again"""

from __future__ import print_function
import time
from opendaq import DAQ, ExpMode, Gains

# Connect to the device
# Change here the serial port in which the openDAQ is connected
daq = DAQ('COM3')

# Set Analog voltage
daq.set_analog(0.9)

stream1 = daq.create_stream(ExpMode.ANALOG_IN, 200, continuous=True)
stream1.analog_setup(pinput=8, gain=Gains.S.x1)

stream2 = daq.create_stream(ExpMode.ANALOG_IN, 300, continuous=True)
stream2.analog_setup(pinput=7, gain=Gains.S.x1)

daq.start()

for i in range(4):
    time.sleep(1)
    print("data1: ", stream1.read())
    print("data2: ", stream2.read())

daq.stop()

stream2.analog_setup(pinput=6, gain=Gains.S.x1)

print("start Again!")
daq.start()

for i in range(4):
    time.sleep(1)
    print("data1: ", stream1.read())
    print("data2: ", stream2.read())

daq.stop()
daq.close()
