import serial
import time
from opendaq import *
import numpy as np


# Connect to the device
dq = DAQ("COM9")  # change for the Serial port in which openDAQ is connected

# ------------------------------------------------------------

preload_buffer = [0.3, 1, 3.3, 2]
burst_source = dq.create_burst()
burst_source.setup(200, len(preload_buffer), 1, 0, 0, 0, 0, False)
dq.load_signal(preload_buffer)

# ------------------------------------------------------------

dq.start()
time.sleep(3)
dq.stop()
