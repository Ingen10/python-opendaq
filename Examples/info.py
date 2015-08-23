from opendaq import DAQ
dq = DAQ("COM3")
dq.set_analog(1)
dq.device_info()
print dq.read_all()
