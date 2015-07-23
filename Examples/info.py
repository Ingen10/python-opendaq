"""Reading the device info """

from opendaq import DAQ
dq = DAQ("/dev/ttyUSB0")
dq.device_info()
print dq.read_all()
