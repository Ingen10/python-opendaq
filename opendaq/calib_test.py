import time
import argparse
import numpy as np
import sys

from opendaq.daq import DAQ
from opendaq.models import InputType, OutputType
from opendaq.daq_model import CalibReg

import logging
from terminaltables import AsciiTable
log_formatter = logging.Formatter("%(message)s")


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
            self.conf_adc(1, 0, 0)
            time.sleep(0.2)
            for idx, g in enumerate(gains):
                self.conf_adc(p, 0, idx)
                time.sleep(.3)
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
                time.sleep(.3)
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
                time.sleep(.3)
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
            time.sleep(.3)
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
            time.sleep(.3)
            pos = len(self.inputs_ids) + i
            calib[idx] = CalibReg(calib[pos].gain, self.read_adc())
        return calib

    def __calib_adc(self, inp_type, pinputs):
        calib = self.get_adc_calib()
        print("CALIB_IN_ADC")
        self.print_calib(calib)
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
        print("CALIB OUT ADC")
        self.print_calib(calib_out)
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
        current_values = [5, 20]
        for idx, o in enumerate(outputs):
            read_values = np.zeros(len(current_values))
            for j, c in enumerate(current_values):
                logging.info("Target: %d mA", c)
                while not yes_no("Connect the analog output %d to the power and press 'y' when ready.\n" % o):
                    pass
                r = self.set_analog(c, o)
                while not(r):
                    while not yes_no("Powering error. Connect AOUT%d to the power and press 'y' when ready.\n" % o):
                        pass
                    r = self.set_analog(c, o)
                read_values[j] = float(raw_input("Enter the measured value (mA): "))
            gain, offset = np.polyfit(current_values, read_values, 1)
            calib[idx] = CalibReg(gain, offset)
        return calib

    def __calib_dac_from_file(self, outputs, calib, dac_file):
        for idx, out in enumerate(outputs):
            set_values = []
            read_values = []
            for row in np.loadtxt(dac_file):
                set_values.append(row[0])
                read_values.append(row[idx + 1])
            gain, offset = np.polyfit(set_values, read_values, 1)
            calib[idx] = CalibReg(gain, offset)
        return calib

    def __calib_dac(self, out_type, outputs, dac_file, meter):
        calib = self.get_dac_calib()
        print("CALIB_IN_DAC")
        self.print_calib(calib)
        if out_type in [OutputType.OUTPUT_TYPE_M, OutputType.OUTPUT_TYPE_S,
                        OutputType.OUTPUT_TYPE_T]:
            calib_out = self.__calib_dac_from_file(outputs, calib, dac_file)
        elif out_type == OutputType.OUTPUT_TYPE_L:
            calib_out = self.__calib_dac_Ltype(outputs, calib)
        print("CALIB_OUT_ADC")
        self.print_calib(calib_out)
        self.set_dac_calib(calib_out)

    def calib_dac(self, file, meter=False):
        for t in OutputType:
            outputs = []
            for idx, out in enumerate(self.outputs_ids):
                if(t == out):
                    outputs.append(idx + 1)
            if outputs:
                self.__calib_dac(t, outputs, file, meter)

    def __test_adc_Atype(self, pinputs):
        gains = self.get_input_gains(pinputs[0])
        read_values = len(pinputs)*[np.zeros(len(gains))]
        error = len(pinputs)*[np.zeros(len(gains))]
        set_values = np.zeros(len(gains))
        set_value_ant = 0
        for idx, g in enumerate(gains):
            max_ref = min(24., 24./g)
            print(g)
            if g <= 2:
                set_values[idx] = 5.
            elif 2 < g <= 16:
                set_values[idx] = 1.
            elif g == 32:
                set_values[idx] = 0.5
            print(set_values[idx])
            print(set_value_ant)
            if(set_value_ant != set_values[idx]):
                while not yes_no("Set %f V at all inputs.\nPress 'y' when ready." % set_values[idx]):
                    pass
                set_value_ant= set_values[idx]
            for j, p in enumerate(pinputs):
                time.sleep(.1)
                self.conf_adc(p, 0, idx)
                read_values[j][idx] = self.read_analog()
                error[j][idx] = abs(100 * (read_values[j][idx] - set_values[idx]) / max_ref)
        print(read_values)
        print(error)

    def __test_adc_AStype(self, pinputs):
        self.__test_adc_Atype(pinputs)

    def __test_adc_MNtype(self, pinputs, istypeN=True):
        gains = self.get_input_gains(pinputs[0])
        read_values = len(pinputs) * [np.zeros(len(gains))]
        error = len(pinputs) * [np.zeros(len(gains))]
        set_values = np.zeros(len(gains))
        for idx, g in enumerate(gains):
            max_ref = min(12., 12./g)
            if istypeN:
                set_values[idx] = 2. / g
            else:
                set_values[idx] = 1. / g
            self.set_analog(set_values[idx])
            for j, p in enumerate(pinputs):
                self.conf_adc(p, 0, idx)
                read_values[j][idx] = self.read_analog()
                error[j][idx] = abs(100 * (read_values[j[idx]] - set_values[idx]) / max_ref)
        print(read_values)
        print(error)

    def __test_adc_Ntype(self, pinputs):
        self.__test_adc_MNtype(pinputs)

    def __test_adc_Mtype(self, pinputs):
        self.__test_adc_MNtype(pinputs, istypeN=False)

    def __test_adc_Stype(self, pinputs):
        set_values = range(5)
        read_values = len(pinputs) * [np.zeros(len(set_values))]
        error = len(pinputs) * [np.zeros(len(set_values))]
        for idx, p in enumerate(pinputs):
            self.conf_adc(p, 0)
            for j, v in enumerate(set_values):
                self.set_analog(v)
                read_values[idx][j] = self.read_analog()
                error[idx][j] = abs(100 * (read_values[idx][j] - v) / 12.)
        print(read_values)
        print(error)

    def __test_adc(self, inp_type, pinputs):
        if inp_type == InputType.INPUT_TYPE_A:
            self.__test_adc_Atype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_AS:
            self.__test_adc_AStype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_M:
            self.__test_adc_Mtype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_S:
            self.__test_adc_Stype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_N:
            self.__test_adc_Ntype(pinputs)

    def test_adc(self):
        for t in InputType:
            inputs = []
            for idx, inp in enumerate(self.inputs_ids):
                if (t == inp):
                    inputs.append(idx + 1)
            if inputs:
                self.__test_adc(t, inputs)

    def __test_dac_Ltype(self, outputs):
        volts = 10.0
        read_values = np.zeros(len(outputs))
        for idx, o in enumerate(outputs):
            while not yes_no("Connect the analog output %d to the power and press 'y' when ready.\n" % o):
                pass
            r = self.set_analog(volts, o)
            while not(r):
                while not yes_no("Powering error. Connect AOUT%d to the power and press 'y' when ready.\n" % o):
                    pass
                r = self.set_analog(volts, o)
            read_values[idx] = float(raw_input("Enter the measured value (mA): "))
        print(read_values)

    def __test_dac_SNM(self, outputs):
        vmin = self.get_adc_types(0).vmin
        vmax = self.get_adc_types(0).vmax
        volts = range(int(vmin), int(vmax), 2)
        read_values = np.zeros(len(volts))
        for idx, v in enumerate(volts):
            self.set_analog(v)
            time.sleep(.5)
            read_values[idx] = raw_input("Enter the measured value: ")
        print(read_values)

    def __test_dac_opendaq_auto(self, outputs, meter):
        vmin = self.get_adc_types(0).vmin
        vmax = self.get_adc_types(0).vmax
        volts = range(int(vmin), int(vmax))
        set_value, read_values = self.measure_dac(volts, meter)

    def __test_dac(self, out_type, outputs, meter):
        if out_type in [OutputType.OUTPUT_TYPE_M, OutputType.OUTPUT_TYPE_S]:
            if meter:
                self.__test_dac_opendaq_auto(outputs, meter)
            else:
                self.__test_dac_SNM(outputs)
        elif out_type == OutputType.OUTPUT_TYPE_L:
            self.__test_dac_Ltype(outputs)

    def test_dac(self, meter):
        for t in OutputType:
            outputs = []
        for idx, out in enumerate(self.outputs_ids):
            if(t == out):
                outputs.append(idx + 1)
        if outputs:
            self.__test_dac(t, outputs, meter)

    def print_calib(self, calib):
        rows = [['Gain', 'Offset']]
        for c in calib:
            rows.append(['%.4f' % c.gain, '%.4f' % c.offset])
        print(AsciiTable(rows).table)


def test_cmd(args):
    daq = CalibDAQ(args.port)
    daq.test_dac(args.meter)
    daq.test_adc()


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

    tparser = subparsers.add_parser('test', help='Test device calibration')
    tparser.set_defaults(func=test_cmd)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
