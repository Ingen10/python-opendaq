#EN TEORIA SERIA ASI, EXACTAMENTE IGUAL QUE EL STREAM, PERO USANDO CREATE_EXTERNAL, PERO NO HACE NADA, IGUAL QUE EN EL EASYDAQ

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

#Connect to the device 
dq = DAQ("COM9") 	#change for the Serial port in which your device is connected
numberPoints=10
pinput=8
ninput=0
nSamples=20
gain= GAINx05

dq.set_analog(0.9)

"""
stream1 = dq.create_stream(1)
#stream1.setup(period, npoints)
stream1.analog_setup(....)

data1 = stream1.read()
data2 = stream2.read()

pylab.plot(data)
"""
dq.create_external(1,0)		#Create a external
dq.setup_channel(1,numberPoints,1)	#configure channel with number the points and run once
dq.conf_channel(1,0,pinput,ninput,gain,nSamples)	
					#Configure number of samples, positive input, negative input
					#gain and number of channel
dq.start()
data = []
channel = []
while True:
	result = dq.get_stream(data,channel)
	if result == 1:
		#data available
		print "New data received -> n Points = ",len(data)
	elif result == 3:
		#stop
		print "Stop received"
		break
#data are raw values from DAC 
print "Values",data

'''
S calibration
'''
gains, offsets = dq.get_cal()
gain = gains[8]
offset = offsets[8]
print "gain = ", gain
print "offset = ", offset
data_mv=[]

for d in data:
    data_mv.append((float(d * gain))/10000 + offset)


time = np.linspace(0,period*len(data_mv),len(data_mv))		
#Define plot, figure and chart
fig = plt.figure()
plt.xlabel("Time (ms)")
plt.ylabel("Voltage (mV)")
plt.title("My chart")
fig.canvas.set_window_title("Example 1")
plt.grid(color='gray',linestyle='dashed')
plt.plot(time,data_mv)
#Lastly show our chart
plt.show()
