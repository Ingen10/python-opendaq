#!/usr/bin/env python

from __future__ import print_function
import os
import time
import logging
import argparse
import numpy as np
from terminaltables import AsciiTable
from . import usbtmc
from .daq import DAQ
from .daq_model import CalibReg, DAQModel

log_formatter = logging.Formatter("%(message)s")


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
        model = DAQModel.new(*self.get_info())
        self.pinputs = model.adc.pinputs
        self.pga_gains = model.adc.pga_gains
        self.dac_slots = model.dac_slots
        self.npios = model.npios
        self.dac_range = (model.dac.vmin, model.dac.vmax)
        self.adc_range = (model.adc.vmin, model.adc.vmax)

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

    def calibrate_dac(self, dac_file=None, meter=None):
        if self.dac_slots < 2:
            if meter:
                volts = range(int(self.dac_range[0]), int(self.dac_range[1]) + 1)
                x, y = self.measure_dac(volts, meter)
                logging.info("Values measured with the USB multimeter:")
            else:
                x, y = np.loadtxt(dac_file, unpack=True)
                logging.info("Values loaded from %s:" % dac_file)

            logging.info(ExpectedValuesTable(zip(x, y)))

            gain, offset = np.polyfit(x, y, 1)
            calib = self.get_dac_calib()[0]
            new_calib = CalibReg(calib.gain*gain, calib.offset + offset)
            self.set_dac_calib([new_calib])

            logging.info("New DAC calibration:")
            self.print_calib([new_calib])
        else:
            x, y, z = np.loadtxt(dac_file, unpack=True)
            logging.info("Values loaded from %s:" % dac_file)

            logging.info(ExpectedValuesTable(zip(x, y)))
            logging.info(ExpectedValuesTable(zip(x, z)))

            gain1, offset1 = np.polyfit(x, y, 1)
            gain2, offset2 = np.polyfit(x, z, 1)

            new_calib = []
            new_calib.append(CalibReg(gain1, offset1))
            new_calib.append(CalibReg(gain2, offset2))

            logging.info("New DAC calibration:")
            self.print_calib(new_calib)
            self.set_dac_calib(new_calib)

    def print_calib(self, calib):
        rows = [['Gain', 'Offset']]
        for c in calib:
            rows.append(['%.4f' % c.gain, '%.4f' % c.offset])
        logging.info(AsciiTable(rows).table)

    def calibrate_adc_offset(self):
        logging.info(title("Calibrating ADC offset"))

        if self.dac_slots < 2:
            self.set_analog(0)
        else:
            while not yes_no("Set 0V at all inputs.\nPress 'y' when ready.\n"):
                pass

        logging.info("0 Volts -->")

        calib = self.get_adc_calib()

        offsets_ampli = []
        for ch in self.pinputs:
            logging.info("AIN %d:" % ch)
            a = []
            b = []
            for i, pga in enumerate(self.pga_gains):
                self.conf_adc(ch, 0, i)
                raw = self.read_adc()
                a.append(pga)
                b.append(raw)
                logging.info("  x%d:\t%d\t%0.4f" % (pga, raw, self.read_analog()))

            corr_gain, corr_offset = np.polyfit(a, b, 1)
            logging.info("m=%1.2f  b=%.2f" % (corr_gain, corr_offset))

            calib[ch - 1] = CalibReg(calib[ch - 1].gain, corr_offset)

            if self.hw_ver != "[M]":
                idx = len(self.pinputs) + ch - 1
                calib[idx] = CalibReg(calib[idx].gain, corr_gain)

            offsets_ampli.append(corr_gain)

        if self.hw_ver == "[M]":
            off = np.mean(offsets_ampli)
            for i, _ in enumerate(self.pga_gains):
                idx = len(self.pinputs) + i
                calib[idx] = CalibReg(calib[idx].gain, off)

        self.set_adc_calib(calib)
        logging.info("ADC calibration updated")

    def calibrate_adc_gain(self):
        logging.info(title("Calibrating ADC gain"))

        if self.dac_slots < 2:
            volts = 2
            self.set_analog(volts)
        else:
            while not yes_no("Set 6V at all inputs.\nPress 'y' when ready."):
                pass
            volts = 6
            self.set_analog(0, 1)
            self.set_analog(0, 2)

        logging.info("%d Volts -->", volts)

        calib = self.get_adc_calib()

        for ch in self.pinputs:
            self.conf_adc(ch, 0, 0)
            time.sleep(.05)
            value = self.read_analog()/volts
            calib[ch - 1] = CalibReg(value, calib[ch - 1].offset)
            logging.info("%d --> %0.4f (%d)" % (ch, value, self.read_adc()))

        if self.hw_ver == "[M]":
            self.set_adc_calib(calib)
            for i, pga in enumerate(self.pga_gains[1:]):
                volts = 1./pga
                self.set_analog(volts)
                logging.info("\nx%1.1f -> %f V", pga, volts)
                a = []
                for ch in self.pinputs:
                    self.conf_adc(ch, 0, i)
                    value = self.read_analog()
                    a.append(value/volts)
                idx = len(self.pinputs) + i + 1
                logging.info("Mean: %f\n", np.mean(a))
                calib[idx] = CalibReg(np.mean(a), calib[idx].offset)

        logging.info("ADC calibration:")
        self.print_calib(calib)
        self.set_adc_calib(calib)

    def calibrate_se(self):
        logging.info("Calibrating ADC (Single-ended mode)")

        calib = self.get_adc_calib()
        volts = [1, 2, 3, 4]

        for ch in self.pinputs:
            logging.info("AIN %d:" % ch)
            self.conf_adc(ch, 0)
            self.read_adc()
            a = []
            b = []
            for v in volts:
                self.set_analog(v)
                val = self.read_analog()
                raw = self.read_adc()
                a.append(raw)
                b.append(val)
                logging.info("%.1f\tV--> == %d %.4f" % (v, raw, val))

            new_corr, _ = np.polyfit(volts, b, 1)
            _, new_offset = np.polyfit(volts, a, 1)
            calib[ch - 1] = CalibReg(new_corr, new_offset)
            logging.info("m: %f\tb: %f" % (new_corr, new_offset))

        logging.info("ADC calibration (single-ended mode):")
        self.print_calib(calib)
        self.set_adc_calib(calib)

    def calibrate_de(self):
        logging.info("Calibrating ADC (Differential-ended mode)")

        calib = self.get_adc_calib()
        ninputs = [2, 1, 4, 3, 6, 5, 8, 7]

        self.set_analog(0)

        for i, ch in enumerate(self.pinputs):
            self.conf_adc(ch, ninputs[i])
            raw = self.read_adc()
            idx = len(self.pinputs) + i
            calib[idx] = CalibReg(calib[idx].gain, raw)

        self.print_calib(calib)
        self.set_adc_calib(calib)

    def test_pio(self):
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
            else:
                logging.error("PIO %d ERROR" % i)

    def test_dac(self, meter=None):
        logging.info(title("DAC calibration test"))

        volts = range(int(self.dac_range[0]), int(self.dac_range[1]) + 1)

        if meter:
            x, y = self.measure_dac(volts, meter)
            logging.info("Values measured with the USB multimeter:")
            logging.info(ExpectedValuesTable(zip(x, y)))
        else:
            for i in volts:
                self.set_analog(i)
                logging.info("Set DAC=%1.1f ->" % i)
                time.sleep(.5)
                if yes_no("Is the voltage correct?"):
                    logging.info("OK")
                else:
                    logging.error("ERROR")

    def test_adc(self):
        logging.info(title("ADC calibration test"))

        if self.hw_ver == "[S]":
            for pinput in self.pinputs:
                self.conf_adc(pinput, 0)
                logging.info("Input: %d:" % pinput)

                rows = [['Target', 'Read', 'Error']]
                for volts in range(5):
                    self.set_analog(volts)
                    val = self.read_analog()
                    err = abs(100 * (val - volts) / 12.)
                    rows.append(['%1.1f V' % volts, '%1.3f V' % val,
                                 '%0.2f %%' % err])
                logging.info(AsciiTable(rows).table)
        elif self.hw_ver in ["TP08", "TP04AR", "TP04AB"]:
            volts = 0
            for i, gain in enumerate(self.pga_gains):
                if gain < 5 and volts != 5:
                    while not yes_no("Set 5 V at all inputs.\nPress 'y' when ready."):
                        pass
                    volts = 5
                elif 5 < gain < 16 and volts != 1:
                    while not yes_no("Set 1 V at all inputs.\nPress 'y' when ready."):
                        pass
                    volts = 1
                elif gain == 32 and volts != 0.5:
                    while not yes_no("Set 0.5 V at all inputs.\nPress 'y' when ready."):
                        pass
                    volts = .5

                max_ref = min(24., 24./gain)
                logging.info("Gain: x%d Target: %.2f V" % (gain, volts))

                rows = [['Input', 'Read', 'Error']]
                for pinput in self.pinputs:
                    self.conf_adc(pinput, 0, i)
                    val = self.read_analog()
                    err = abs(100 * (val - volts) / max_ref)
                    rows.append([pinput, '%1.3f V' % val, '%0.2f %%' % err])
                logging.info(AsciiTable(rows).table)
        else:
            for i, gain in enumerate(self.pga_gains):
                if self.hw_ver == '[N]':
                    volts = 2. / gain
                else:
                    volts = 1. / gain
                max_ref = min(12., 12./gain)

                self.set_analog(volts)
                logging.info("Gain: x%0.2f Target: %.2f V" % (gain, volts))

                rows = [['Input', 'Read', 'Error']]
                for pinput in self.pinputs:
                    self.conf_adc(pinput, 0, i)
                    val = self.read_analog()
                    err = abs(100 * (val - volts) / max_ref)
                    rows.append([pinput, '%1.3f V' % val, '%0.2f %%' % err])
                logging.info(AsciiTable(rows).table)


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

    daq.set_analog(args.volts)

    if args.interactive:
        print("Press Ctrl-C to exit")
        try:
            while True:
                print("Enter new voltage: ", end='')
                try:
                    daq.set_analog(float(raw_input()))
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
        if daq.dac_slots < 2:
            daq.test_dac(meter)
        daq.test_adc()
        if daq.npios > 0:
            daq.test_pio()
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
        daq.calibrate_dac(dac_file=args.file, meter=meter)
    else:
        logging.info("Resetting calibration values")
        daq.reset_calib()

        logging.info(title("Calibrating DAC"))

        meter = usbtmc.RigolDM3058(args.meter) if args.auto else None
        daq.calibrate_dac(dac_file=args.file, meter=meter)

        if daq.hw_ver == "[S]":
            pass
            daq.calibrate_se()
            daq.calibrate_de()
        else:
            daq.calibrate_adc_offset()
            daq.calibrate_adc_gain()


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
    tparser.add_argument('-a', '--auto', action='store_true',
                         help='Automated testing using a USB multimeter')
    tparser.set_defaults(func=lambda args: calib_cmd(args, True))

    # 'set-voltage' command parser
    vparser = subparsers.add_parser('set-voltage', help='Set DAC voltage')
    vparser.add_argument('-i', '--interactive', action='store_true',
                         help='Interactively ask for voltage values')
    vparser.add_argument('volts', type=float, help='Output voltage')
    vparser.set_defaults(func=set_voltage_cmd)

    # 'serial' command parser
    sparser = subparsers.add_parser('serial', help='Read or write the serial number')
    sparser.add_argument('-w', '--write', dest='serial', type=int,
                         help='Write a new serial number')
    sparser.set_defaults(func=serial_cmd)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
