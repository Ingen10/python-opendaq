import serial
import matplotlib
import matplotlib.pyplot as plt
from opendaq import *
import numpy as np

GAINx05  = 0
GAINx1   = 1
GAINX2   = 2
GAINx10  = 3
GAINx100 = 4

# Connect to the device
dq = DAQ("COM9")  # Change for the Serial port in which your device is
period = 200
numberPoints = 20
pinput = 8
ninput = 0
nSamples = 20
gain = GAINx05

dq.set_analog(0.9)


dq.create_stream(1, period)	 # Create a stream
dq.setup_channel(1, numberPoints, 1)    # Configure channel with number the
                                        # points and run once
dq.conf_channel(1, 0, pinput, ninput, gain, nSamples)
                    # Configure number of samples, positive input, negative
                    # input, gain and number of channel

csv_buffer = [0.3, 1, 1.6]

dq.create_stream(4, 200)
dq.setup_channel(4, len(csv_buffer), False)
dq.conf_channel(4, 1, 0, 0, 0, 0)
dq.load_signal(csv_buffer, 0)

dq.start()
data = []
channel = []
while True:
    result = dq.get_stream(data, channel)
    if result == 1:
        # Data available
        print "New data received -> n Points = ", len(data)
    elif result == 3:
        # Stop
        print "Stop received"
        break
# Data are raw values from DAC
print "Values", data

'''
S calibration
'''
gains, offsets = dq.get_cal()
gain = gains[8]
offset = offsets[8]
print "gain = ", gain
print "offset = ", offset
data_mv = []

for d in data:
    data_mv.append((float(d * gain))/10000 + offset)


time = np.linspace(0, period * len(data_mv), len(data_mv))
# Define plot, figure and chart
fig = plt.figure()
plt.xlabel("Time (ms)")
plt.ylabel("Voltage (mV)")
plt.title("My chart")
fig.canvas.set_window_title("Example 1")
plt.grid(color='gray', linestyle='dashed')
plt.plot(time, data_mv)
# Lastly show our chart
plt.show()
