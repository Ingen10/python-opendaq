#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import time
import logging
import argparse
import numpy as np
import json
from terminaltables import AsciiTable
from . import usbtmc
from .daq import DAQ
from .daq_model import CalibReg
from .models import InputType, OutputType

log_formatter = logging.Formatter("%(message)s")

if sys.version_info[:2] > (2, 7):
    raw_input = input


class ExpectedValuesTable(AsciiTable):
    '''A custom AsciiTable for printing calibration results'''
    def __init__(self, values):
        rows = [['Target', 'Read']]
        for x, y in values:
            rows.append(['%.1f V' % x, '%.4f V' % y])

        AsciiTable.__init__(self, rows)

    def __str__(self):
        return self.table


def title(text):
    return '\n' + text + '\n' + '-'*len(text)


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

        """
        self.pinputs = model.adc.pinputs
        self.pga_gains = model.adc.pga_gains.values
        self.dac_slots = model.dac_slots
        self.npios = model.npios
        self.dac_range = (model.dac.vmin, model.dac.vmax)
        self.adc_range = (model.adc.vmin, model.adc.vmax)
        """

    def read_analog(self):
        self.read_adc()
        time.sleep(0.05)
        return DAQ.read_analog(self)

    def reset_calib(self):
        adc_calib = self.get_adc_calib()
        dac_calib = self.get_dac_calib()
        self.set_adc_calib([CalibReg(1., 0.)]*len(adc_calib))
        self.set_dac_calib([CalibReg(1., 0.)]*len(dac_calib))

    def measure_dac(self, values, meter):
        y = []
        for v in values:
            self.set_analog(v)
            time.sleep(0.1)
            y.append(meter.measure('volt_dc'))
        return values, y

    def __calibrate_dac_auto_opendaq(self, meter):
        volts = range(int(self.outputs[0].vmin), int(self.outputs[0].vmax) + 1)
        x, y = self.measure_dac(volts, meter)
        return np.polyfit(x, y, 1)

    def __calibrate_dac_fromfile(self, index, dac_file):
        set_values = []
        read_values = []
        for row in np.loadtxt(dac_file):
            set_values.append(row[0])
            read_values.append(row[index])
        return np.polyfit(set_values, read_values, 1)

    def __load_calib_json(self, file_type='calib'):
        filename = '%s_%s_%s.json' % (self.serial_str, time.strftime('%y%m%d'), file_type)
        file_created = True
        try:
            f = open(filename, 'r')
        except FileNotFoundError:
            file_created = False
        if file_created:
            data = json.load(f)
        else:
            f = open(filename, 'w')
            data = {}
            data['model'] = self.model_str
            data['serial'] = self.serial
            data['time'] = int(time.time())
            if file_type == 'calib':
                data['humidity'] = int(raw_input('Enter humidity (%): '))
                data['temperature'] = float(raw_input('Enter temperature: '))
        return f, data

    def calibrate_dac(self, dac_file=None, meter=None, report=False):
        if report:
            f, data = self.__load_calib_json()
            outputs = []
        new_calib = [CalibReg(1., 0.)] * self.dac_slots
        self.set_dac_calib(new_calib)
        for idx, i in enumerate(self.outputs_ids):
            if i in [OutputType.OUTPUT_TYPE_M, OutputType.OUTPUT_TYPE_S] and meter:
                logging.info("Values measured with the USB multimeter:")
                gain, offset = self.__calibrate_dac_auto_opendaq(meter)
            else:
                logging.info("Values loaded from %s:" % dac_file)
                gain, offset = self.__calibrate_dac_fromfile(idx, dac_file)
            print(idx)
            new_calib[idx] = CalibReg(gain, offset)
            if report:
                outputs.append({'gain': round(gain, 4), 'offset': round(offset, 4)})
        self.set_dac_calib(new_calib)
        logging.info("New DAC calibration:")
        self.print_calib(new_calib)
        if report:
            data['outputs'] = outputs
            json.dump(data, f, indent=2)
            f.close()

    def print_calib(self, calib):
        rows = [['Gain', 'Offset']]
        for c in calib:
            rows.append(['%.4f' % c.gain, '%.4f' % c.offset])
        logging.info(AsciiTable(rows).table)

    def __calibrate_adc_DAQS(self, pinput):
        volts = [1, 2, 3, 4]
        ninputs = [2, 1, 4, 3, 6, 5, 8, 7]
        self.conf_adc(pinput, 0)
        self.read_adc()
        analog_read, raw_read = 2*[np.zeros(len(volts))]
        for idx, v in enumerate(volts):
            self.set_analog(v)
            analog_read[idx] = self.read_analog()[0]
            raw_read[idx] = self.read_adc()
        dcgain = np.polyfit(volts, analog_read, 1)[0]
        offset1 = np.polyfit(volts, raw_read, 1)[1]
        self.set_analog(0)
        self.conf_adc(pinput, ninputs[pinput-1])
        offset2 = self.read_adc()
        return dcgain, 1, offset1, offset2

    def __calibrate_adc_offset(self, pinput):
        gains = self.get_input_gains(pinput)
        raw_read = np.zeros(len(gains))
        for idx, g in enumerate(gains):
            self.conf_adc(pinput, 0, idx)
            raw_read[idx] = self.read_adc()
        return np.polyfit(gains, raw_read, 1)

    def __calibrate_adc_gain(self, pinput, volts, mode=0):
        self.conf_adc(pinput, mode, 0)
        return self.read_analog()[0] / volts

    def __calibrate_adc_DAQMN(self, pinput):
        self.set_analog(0)
        offset2, offset1 = self.__calibrate_adc_offset(pinput)
        volts = 2
        self.set_analog(volts)
        dcgain = self.__calibrate_adc_gain(pinput, volts)
        return dcgain, 1, offset1, offset2

    def __calibrate_adc_A_offset(self, pinput):
        offset2, offset1 = self.__calibrate_adc_offset(pinput)
        return offset1, offset2

    def __calibrate_adc_A_gain(self, pinput):
        dcgain2 = 1
        volts = 6
        dcgain = self.__calibrate_adc_gain(pinput, volts)
        if self.get_adc_types(pinput)._input_id == InputType.INPUT_TYPE_AS:
            dcgain2 = self.__calibrate_adc_gain(pinput, volts, 1)
        return dcgain, dcgain2

    def __calibrate_adc_gain2_M(self, gain_idx):
        volts = 1./self. get_input_gains(gain_idx)
        self.set_analog(volts)
        logging.info("\nx%1.1f -> %f V", self. get_input_gains(gain_idx), volts)
        a = np.zeros(len(self.inputs))
        for idx in len(a):
            self.conf_adc(idx + 1, 0, gain_idx)
            a.append(self.read_analog()[0]/volts)
        return np.mean(a)

    def calibrate_adc(self, report=False):
        if len(self.inputs_ids) == 0:
            return
        if report:
            f, data = self.__load_calib_json()
            inputs = []
        calib = [CalibReg(1., 0.)]*self.adc_slots
        self.set_adc_calib(calib)
        if self.inputs_ids[0] == InputType.INPUT_TYPE_M:
            offset2_mean = np.zeros(len(self.inputs_ids))
        if self.inputs_ids[0] in [InputType.INPUT_TYPE_M, InputType.INPUT_TYPE_S, InputType.INPUT_TYPE_N]:
            for idx, i in enumerate(self.inputs_ids):
                if i == InputType.INPUT_TYPE_S:
                    offset1, offset2 = self.__calibrate_adc_DAQS(idx + 1)
                else:
                    dcgain, dcgain2 = self.__calibrate_adc_DAQMN(idx + 1)
                    if InputType.INPUT_TYPE_M:
                        offset2_mean[idx] = offset2
                calib[idx] = CalibReg(dcgain, offset1)
                calib[(idx + len(self.inputs_ids))] = CalibReg(dcgain2, offset2)
            if i == InputType.INPUT_TYPE_M:
                offset2 = np.mean(offset2_mean)
                for i in range(1, len(self. get_input_gains(0))):
                    dcgain2 = self.__calibrate_adc_gain_M(i)
                    calib[(i - 1 + len(self.inputs_ids))] = CalibReg(dcgain2, offset2)
        else:
            while not yes_no("Set 0V at all inputs.\nPress 'y' when ready."):
                pass
            for idx, i in enumerate(self.inputs_ids):
                offset2, offset1 = self.__calibrate_adc_offset(idx + 1)
                calib[idx] = CalibReg(1.0, offset1)
                calib[(idx + len(self.inputs_ids))] = CalibReg(1.0, offset2)
            while not yes_no("Set 6V at all inputs.\nPress 'y' when ready."):
                pass
            for idx, i in enumerate(self.inputs_ids):
                dcgain1, dcgain2 = self.__calibrate_adc_A_gain(idx + 1)
                calib[idx] = CalibReg(dcgain1, calib[idx][1])
                calib[(idx + len(self.inputs_ids))] = CalibReg(dcgain2, calib[(idx + len(self.inputs_ids))][1])
        self.set_adc_calib(calib)


    def test_pio(self, report=False):
        if report:
            f = open('%s_%s_test.json' % (self.serial_str, time.strftime('%y%m%d')), 'r')
            data = json.load(f)
            pios = []
        logging.info(title("PIO test"))

        self.set_port_dir(0)
        for i in range(1, 7):
            self.set_pio_dir(i, 1)
            self.set_pio(i, 0)
            port_down = self.read_port()
            self.set_pio(i, 1)
            port_up = self.read_port()
            self.set_pio_dir(i, 0)

            if port_down == 0 and port_up == 0x3f:
                logging.info("PIO %d OK" % i)
                if report:
                    pios.append({'PIO %d' % i: 'OK'})
            else:
                logging.error("PIO %d ERROR" % i)
                if report:
                    pios.append({'PIO %d' % i: 'ERROR'})
        if report:
            data['pios'] = pios
            f = open('%s_%s_test.json' % (self.serial_str, time.strftime('%y%m%d')), 'w')
            json.dump(data, f, indent=2)
            f.close()

    def __test_dac_opendaq_auto(self, meter, report):
        out = self.get_dac_types(0)
        volts = range(int(out.vmin), int(out.vmax) + 1)
        x, y = self.measure_dac(volts, meter)
        logging.info("Values measured with the USB multimeter:")
        logging.info(ExpectedValuesTable(zip(x, y)))
        if report:
            items = {'dc_range': dac_range, 'number': 1, 'type': 'voltage_output',
                     'unit': 'V', 'readings': []}
            for i, value in enumerate(x):
                items['readings'].append({'dc_ref': value,
                                          'dc_read': round(y[i], 4)})
        return items

    def __test_dac_L(self, output, ref):
        while not yes_no("Connect the analog output %d to the power and press 'y' when ready.\n" % output):
            pass
        r = self.set_analog(ref, output)
        while not(r):
            while not yes_no("Powering error. Connect AOUT%d to the power and press 'y' when ready.\n" % output):
                pass
            r = self.set_analog(ref, output)
        read_value = float(raw_input("Enter the measured value (mA): "))
        return read_value

    def _test_dac_manual(self, output):
        out = self.get_dac_types(output)
        volts = range(int(out.vmin), int(out.vmax) + 1, 2)
        for v in volts:
            self.set_analog(v, output)
            logging.info("Set DAC=%1.1f ->" % v)
            time.sleep(.5)

    def test_dac(self, meter=None, report=False):
        logging.info(title("DAC calibration test"))
        if meter and self.outputs_ids[0] in [OutputType.OUTPUT_TYPE_M, OutputType.OUTPUT_TYPE_S]:
            items = self.__test_dac_opendaq_auto(meter, report)
        else:
            for idx, o in enumerate(self.outputs_ids):
                if o == OutputType.OUTPUT_TYPE_L:
                    read_value = self.__test_dac_L(idx+1, 10)
                else:
                    self.__test_dac_manual(idx+1)

    def __test_adc_DAQS(self, pinput):
        volts = range(5)
        read_value, err = 2*[np.zeros(len(volts))]
        self.conf_adc(pinput, 0)
        vmax_p = float(self.get_adc_types(pinput).vmax)
        for v in volts:
            self.set_analog(v)
            read_value[v] = self.read_analog()[0]
            err[v] = abs(100 * (read_value[v] - v) / vmax_p)
        return read_value, err

    def __test_adc_DAQNM(self, pinput, gain):
        gains = self. get_input_gains(pinput)
        read_value, err = np.zeros(len(gains))
        for idx, g in enumerate(gains):
            if self.get_adc_types(pinput)._input_id == InputType.INPUT_TYPE_N:
                volts = 2. / g
            else:
                volts = 1. / g
            max_ref = min(12., 12./g)
            self.set_analog(volts)
            read_value[idx] = self.read_analog()[0]
            err[idx] = abs(100 * (read_value[idx] - volts) / max_ref)
        return read_value, err

    def test_adc_A(self, pinput, gain, volts):
        gains = self. get_input_gains(pinput)
        max_ref = min(24.0, 24.0/gains[gain])
        self.conf_adc(pinput, 0, gain)
        read_value = self.read_analog()[0]
        err = abs(100 * (read_value - volts) / max_ref)
        return read_value, err

    def test_adc(self, report=False):
        if len(self.inputs_ids) == 0:
            return
        if self.inputs_ids[0] in [InputType.INPUT_TYPE_M, InputType.INPUT_TYPE_S, InputType.INPUT_TYPE_N]:
            for idx, i in enumerate(self.inputs_ids):
                if i == InputType.INPUT_TYPE_S:
                    read_value, err = self.__test_adc_DAQS(idx + 1)
                else:
                    read_value, err = self.__test_adc_DAQNM(idx + 1)
        else:
            gains = self. get_input_gains(0)
            volts = 0
            for idx, g in enumerate(gains):
                if g < 4 and volts != 5:
                    volts = 5
                elif 4 < g < 16 and volts != 1:
                    volts = 1
                elif g == 32 and volts != 0.5:
                    volts = .5
                while not yes_no("Set %f V at all inputs.\nPress 'y' when ready." % volts):
                    pass
                for j, p in enumerate(self.inputs_ids):
                    read_value, err = self.test_adc_A(j + 1, idx, volts)


def info_cmd(args):
    daq = CalibDAQ(args.port)
    logging.info(daq)


def serial_cmd(args):
    daq = CalibDAQ(args.port)

    if args.serial:
        daq.set_id(args.serial)
        logging.info("Serial number was changed")
    else:
        logging.info(daq.serial_str)


def set_voltage_cmd(args):
    daq = CalibDAQ(args.port)
    channels = []
    if not args.channel:
        channels = range(1, daq.dac_slots + 1)
    else:
        channels.append(args.channel)
    for ch in channels:
        daq.set_analog(args.volts, ch)
    if args.interactive:
        print("Press Ctrl-C to exit")
        try:
            while True:
                if daq.model_str == 'EM08C-RRLL':
                    print("Enter new current (mA): ", end='')
                else:
                    print("Enter new voltage (V): ", end='')
                value = float(raw_input())
                for ch in channels:
                    print(ch)
                    try:
                        daq.set_analog(value, ch)
                        time.sleep(.1)
                    except ValueError:
                        print("Invalid value!")
        except KeyboardInterrupt:
            pass


def calib_cmd(args, test=False):
    daq = CalibDAQ(args.port)
    if args.log:
        # setup the file logger
        filename = '%s_%s.log' % (daq.serial_str, time.strftime('%y%m%d'))

        if os.path.exists(filename):
            os.remove(filename)

        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(log_formatter)
        logging.getLogger().addHandler(file_handler)

    if test:
        meter = usbtmc.RigolDM3058(args.meter) if args.auto else None
        if daq.dac_slots != 2:  # only devices with tacho trigger DAC have 2 outputs
            daq.test_dac(meter, args.json)
        if daq.hw_ver != "EM08C-RRLL":
            daq.test_adc(args.json)
        if daq.hw_ver in ["[S]", "[N]", "[M]"]:
            daq.test_pio(args.json)
    elif args.show:
        logging.info(title("DAC calibration"))
        daq.print_calib(daq.get_dac_calib())
        logging.info(title("ADC calibration"))
        daq.print_calib(daq.get_adc_calib())
    elif args.reset:
        logging.info("Resetting calibration values")
        daq.reset_calib()
    elif args.dac:
        logging.info(title("Calibrating DAC"))
        meter = usbtmc.RigolDM3058(args.meter) if args.auto else None
        daq.calibrate_dac(dac_file=args.file, meter=meter, report=args.json)
    else:
        logging.info("Resetting calibration values")
        daq.reset_calib()

        logging.info(title("Calibrating DAC"))

        meter = usbtmc.RigolDM3058(args.meter) if args.auto else None
        daq.calibrate_dac(dac_file=args.file, meter=meter, report=args.json)

        daq.calibrate_adc(args.json)

        """
        if daq.hw_ver == "[S]":
            pass
            daq.calibrate_se(args.json)
            daq.calibrate_de(args.json)
        elif daq.hw_ver != "EM08C-RRLL":
            daq.calibrate_adc_offset(args.json)
            daq.calibrate_adc_gain(args.json)
        """


def main():
    # setup the logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='/dev/ttyUSB0',
                        help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('-m', '--meter', default='/dev/usbtmc0',
                        help='USBTMC port of a digital multimeter for '
                        'performing fully automated tests. Currently, '
                        'only the Rigol DM3058 has been tested.'
                        '(default: /dev/usbtmc0).')
    subparsers = parser.add_subparsers(title='Subcommands')

    # 'info' command parser
    iparser = subparsers.add_parser('info', help='Show device information')
    iparser.set_defaults(func=info_cmd)

    # 'calib' command parser
    cparser = subparsers.add_parser('calib', help='Calibrate the devices')
    cparser.add_argument('-l', '--log', action='store_true',
                         help='Generate log file'),
    cparser.add_argument('-j', '--json', action='store_true',
                         help='Generate json file'),
    cparser.add_argument('-r', '--reset', action='store_true',
                         help='Reset calibration values')
    cparser.add_argument('-d', '--dac', action='store_true',
                         help='Apply DAC calibration and exit')
    cparser.add_argument('-f', '--file', default='calib.txt',
                         help='Select file source to load DAC parameters'
                         '(default: calib.txt)')
    cparser.add_argument('-s', '--show', action='store_true',
                         help='Show calibration values')
    cparser.add_argument('-a', '--auto', action='store_true',
                         help='Automated calibration using a USB multimeter')

    cparser.set_defaults(func=calib_cmd)

    # 'test' command parser
    tparser = subparsers.add_parser('test', help='Test device calibration')
    tparser.add_argument('-l', '--log',
                         help='Generate log file', action='store_true')
    tparser.add_argument('-j', '--json',
                         help='Generate json file', action='store_true')
    tparser.add_argument('-a', '--auto', action='store_true',
                         help='Automated testing using a USB multimeter')
    tparser.set_defaults(func=lambda args: calib_cmd(args, True))

    # 'set-voltage' command parser
    vparser = subparsers.add_parser('set-voltage', help='Set DAC voltage')
    vparser.add_argument('-i', '--interactive', action='store_true',
                         help='Interactively ask for voltage values')
    vparser.add_argument('volts', type=float, help='Output voltage')
    vparser.add_argument('-ch', '--channel', type=int, help='Output channel')
    vparser.set_defaults(func=set_voltage_cmd)

    # 'serial' command parser
    sparser = subparsers.add_parser('serial', help='Read or write the serial number')
    sparser.add_argument('-w', '--write', dest='serial', type=int,
                         help='Write a new serial number')
    sparser.set_defaults(func=serial_cmd)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
