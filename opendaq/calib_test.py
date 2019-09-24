import time
import argparse
import numpy as np
import sys

from opendaq.daq import DAQ
from opendaq.models import InputType, OutputType
from opendaq.daq_model import CalibReg


if sys.version_info[:2] > (2, 7):
    raw_input = input


def yes_no(question):
    print('%s [y/n]' % question)
    while True:
        answer = raw_input().lower()
        if answer in ('y', 'n'):
            return answer == 'y'
        else:
            print("Please respond with 'y' or 'n'.")


class CalibDAQ(DAQ):
    def __init__(self, port):
        DAQ.__init__(self, port)
        self.outputs_ids = [self.get_dac_types(i)._output_id for i in range(len(self.get_dac_types()))]
        self.inputs_ids = [self.get_adc_types(i)._input_id for i in range(len(self.get_adc_types()))]

        self.serial = self.get_info()[2]

        self.adc_slots, self.dac_slots = self.get_slots()

    def read_analog(self):
        self.read_adc()
        time.sleep(0.05)
        return DAQ.read_analog(self)[0]

    def reset_calib(self):
        adc_calib = self.get_adc_calib()
        dac_calib = self.get_dac_calib()
        self.set_adc_calib([CalibReg(1., 0.)]*len(adc_calib))
        self.set_dac_calib([CalibReg(1., 0.)]*len(dac_calib))

    def __calib_adc_ANtype(self, pinputs, calib, isAtype=True):
        volts = 0.0
        if (isAtype):
            while not yes_no("Set %dV at all inputs.\nPress 'y' when ready.\n" % volts):
                pass
        else:
            self.set_analog(volts)
        for p in pinputs:
            gains = self.get_input_gains(p)
            raw_read = np.zeros(len(gains))
            for idx, g in enumerate(gains):
                self.conf_adc(p, 0, idx)
                raw_read[idx] = self.read_adc()
            corr_gain, corr_offset = np.polyfit(gains, raw_read, 1)
            calib[p - 1] = CalibReg(calib[p - 1].gain, corr_offset)
            pos = len(self.inputs_ids) + p - 1
            calib[pos] = CalibReg(calib[pos].gain, corr_gain)
        if (isAtype):
            volts = 6.0
            while not yes_no("Set %dV at all inputs.\nPress 'y' when ready.\n" % volts):
                pass
        else:
            volts = 2.0
            self.set_analog(volts)
        for p in pinputs:
            self.conf_adc(p, 0, 0)
            time.sleep(.3)
            calib[p - 1] = CalibReg((self.read_analog()/volts), calib[p - 1].offset)
        return calib

    def __calib_adc_Atype(self, pinputs, calib):
        print("ENTRADAS TIPO A")
        print(pinputs)
        return self.__calib_adc_ANtype(pinputs, calib)

    def __calib_adc_Ntype(self, pinputs, calib):
        # Igual que A
        print("ENTRADAS TIPO N")
        print(pinputs)
        return self.__calib_adc_ANtype(pinputs, calib, isAtype=False)

    def __calib_adc_AStype(self, pinputs, calib):
        print("ENTRADAS TIPO AS")
        print(pinputs)
        self.__calib_adc_Atype(pinputs, calib)
        print("CALIB SHUNTS")
        return calib

    def __calib_adc_Mtype(self, pinputs, calib):
        print("ENTRADAS TIPO M")
        print(pinputs)
        volts = 0.0
        self.set_analog(volts)
        for j, p in enumerate(pinputs):
            gains = self.get_input_gains(p)
            raw_read = np.zeros(len(gains))
            corr_gain = np.zeros(len(gains))
            for idx, g in enumerate(gains):
                self.conf_adc(p, 0, idx)
                raw_read[idx] = self.read_adc()
            corr_gain[j], corr_offset = np.polyfit(gains, raw_read, 1)
            calib[p - 1] = CalibReg(calib[p - 1].gain, corr_offset)
        mean_corr_gain = np.mean(corr_gain)
        for i in range(len(corr_gain)):
            pos = len(self.inputs_ids) + i
            calib[pos] = CalibReg(calib[pos].gain, mean_corr_gain)
        for i, pga in enumerate(gains[1:]):
            volts = 1./pga
            self.set_analog(volts)
            read_value = np.zeros(len(pinputs))
            for j, p in enumerate(pinputs):
                self.conf_adc(p, 0, i)
                read_value[j] = self.read_analog() / volts
            pos = len(self.inputs_ids) + i + 1
            calib[pos] = CalibReg(np.mean(read_value), calib[idx].offset)
        return calib

    def __calib_adc_Stype(self, pinputs, calib):
        print("ENTRADAS TIPO S")
        print(pinputs)
        volts = [1., 2., 3., 4.]
        for p in pinputs:
            self.conf_adc(p, 0)
            read_raw = np.zeros(len(volts))
            read_analog = np.zeros(len(volts))
            for idx, v in enumerate(volts):
                self.set_analog(v)
                read_analog[idx] = self.read_analog()
                read_raw[idx] = self.read_adc()
            new_corr = np.polyfit(volts, read_analog, 1)[0]
            new_offset = np.polyfit(volts, read_raw, 1)[1]
            calib[p - 1] = CalibReg(new_corr, new_offset)
        self.set_analog(0)
        ninputs = [2, 1, 4, 3, 6, 5, 8, 7]
        for i, p in enumerate(pinputs):
            self.conf_adc(p, ninputs[i])
            pos = len(self.inputs_ids) + i
            calib[idx] = CalibReg(calib[pos].gain, self.read_adc())
        return calib

    def __calib_adc(self, inp_type, pinputs):
        calib = self.get_adc_calib()
        if inp_type == InputType.INPUT_TYPE_A:
            calib_out = self.__calib_adc_Atype(pinputs, calib)
        elif inp_type == InputType.INPUT_TYPE_AS:
            calib_out = self.__calib_adc_AStype(pinputs, calib)
        elif inp_type == InputType.INPUT_TYPE_M:
            calib_out = self.__calib_adc_Mtype(pinputs, calib)
        elif inp_type == InputType.INPUT_TYPE_S:
            calib_out = self.__calib_adc_Stype(pinputs, calib)
        elif inp_type == InputType.INPUT_TYPE_N:
            calib_out = self.__calib_adc_Ntype(pinputs, calib)
        print(calib_out)
        self.set_adc_calib(calib_out)

    def calib_adc(self):
        for t in InputType:
            inputs = []
            for idx, inp in enumerate(self.inputs_ids):
                if (t == inp):
                    inputs.append(idx + 1)
            if inputs:
                self.__calib_adc(t, inputs)

    def __calib_dac_Ltype(self, outputs, calib):
        print("SALIDAS TIPO L")
        print(outputs)
        return calib

    def __calib_dac_from_file(self, outputs, calib, dac_file):
        for idx, out in enumerate(outputs):
            set_values = []
            read_values = []
            for row in np.loadtxt(dac_file):
                set_values.append(row[0])
                read_values.append(row[idx + 1])
            gain, offset =  np.polyfit(set_values, read_values, 1)
            calib[idx] = CalibReg(gain, offset)
        return calib

    def __calib_dac(self, out_type, outputs, dac_file, meter):
        calib = self.get_dac_calib()
        if out_type in [OutputType.OUTPUT_TYPE_M, OutputType.OUTPUT_TYPE_S,
                        OutputType.OUTPUT_TYPE_L]:
            calib_out = self.__calib_dac_from_file(outputs, calib, dac_file)
        elif out_type == OutputType.OUTPUT_TYPE_L:
            calib_out = self.__calib_dac_Ltype(outputs, calib)
        print(calib_out)
        self.set_dac_calib(calib_out)

    def calib_dac(self, file, meter=False):
        for t in OutputType:
            outputs = []
            for idx, out in enumerate(self.outputs_ids):
                if(t == out):
                    outputs.append(idx + 1)
            if outputs:
                self.__calib_dac(t, outputs, file, meter)


def calib_cmd(args):
    daq = CalibDAQ(args.port)
    daq.reset_calib()
    daq.calib_dac(args.file, args.meter)
    daq.calib_adc()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='/dev/ttyUSB0',
                        help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('-m', '--meter', default='/dev/usbtmc0',
                        help='USBTMC port of a digital multimeter for '
                        'performing fully automated tests. Currently, '
                        'only the Rigol DM3058 has been tested.'
                        '(default: /dev/usbtmc0).')
    subparsers = parser.add_subparsers(title='Subcommands')
    cparser = subparsers.add_parser('calib', help='Calibrate the devices')
    cparser.add_argument('-f', '--file', default='calib.txt',
                         help='Select file source to load DAC parameters'
                         '(default: calib.txt)')
    cparser.set_defaults(func=calib_cmd)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
