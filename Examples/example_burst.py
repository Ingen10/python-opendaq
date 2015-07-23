""" This example shows how create a burst experiment. It outputs a predefined signal through 
    one analog output.
"""
from opendaq import *
from opendaq.daq import *
import time


# Connect to the device
dq = DAQ("COM9")  # change for the Serial port in which openDAQ is connected

preload_buffer = [0.3, 1, 3.3, 2]

burst_source = dq.create_burst(mode=ANALOG_OUTPUT, period=200, npoints=len(preload_buffer), continuous=False)

burst_source.analog_setup()

burst_source.load_signal(preload_buffer)

dq.start()

time.sleep(3)

dq.stop()
