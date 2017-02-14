from __future__ import print_function
import os

# function modes
FUNCTIONS = {
    'volt_dc': 'VOLTage:DC',
    'volt_ac': 'VOLTage:AC',
    'curr_dc': 'CURRent:DC',
    'curr_ac': 'CURRent:AC',
    'frequency': 'FREQuency',
    'resistance': 'RESistance',
    'continuity': 'CONTinuity',
    'capacitance': 'CAPacitance',
    'diode': 'diODe',
}


class usbtmc:
    """Simple implementation of a USBTMC device driver,
    in the style of visa.h
    """

    def __init__(self, device):
        self.device = device
        self.FILE = os.open(device, os.O_RDWR)

        # TODO: Test that the file opened

    def write(self, command):
        os.write(self.FILE, bytearray(command, 'ascii'))

    def read(self, length=4000):
        return os.read(self.FILE, length)

    def getName(self):
        self.write("*IDN?")
        return str(self.read(300))

    def sendReset(self):
        self.write("*RST")


class RigolDM3058:
    """Class for controlling a Rigol DS1000 series oscilloscope"""

    def __init__(self, device):
        self.__dev = usbtmc(device)
        self.name = self.__dev.getName()
        self.reset()
        self.write('cmdset rigol')
        self.write(':MEASure:VOLTage:DC range 2')

    def write(self, command):
        """Send an arbitrary command directly to the scope"""
        self.__dev.write(command)

    def read(self, command):
        """Read an arbitrary amount of data directly from the scope"""
        return self.__dev.read(command)

    def set_function(self, function):
        """Select the measure function type"""
        command = ':FUNCtion:' + FUNCTIONS[function]
        self.write(command)

    def measure(self, function):
        command = ':MEASure:%s?' % FUNCTIONS[function]
        self.write(command)
        return float(self.read(13))

    def reset(self):
        """Reset the instrument"""
        self.__dev.sendReset()


if __name__ == "__main__":
    rigol = RigolDM3058("/dev/usbtmc1")
    print(rigol.name)

    for i in range(10):
        print(rigol.measure('volt_dc'))
