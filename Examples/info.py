from opendaq import DAQ
dq = DAQ("COM3")
dq.device_info()
print dq.read_all()
