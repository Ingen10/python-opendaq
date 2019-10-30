import sys
import logging
import time

import argparse

from . import usbtmc
from .calib import Calib
from .test import Test
from .daq import DAQ

log_formatter = logging.Formatter("%(message)s")

if sys.version_info[:2] > (2, 7):
    raw_input = input


def title(text):
    return '\n' + text + '\n' + '-'*len(text)


def info_cmd(args):
    daq = DAQ(args.port)
    logging.info(daq)


def serial_cmd(args):
    daq = DAQ(args.port)

    if args.serial:
        daq.set_id(args.serial)
        logging.info("Serial number was changed")
    else:
        logging.info(daq.serial_str)


def set_voltage_cmd(args):
    daq = DAQ(args.port)
    channels = []
    if not args.channel:
        channels = range(1, daq.get_slots()[1] + 1)
    else:
        channels.append(args.channel)
    for ch in channels:
        daq.set_analog(args.volts, ch)
    if args.interactive:
        print("Press Ctrl-C to exit")
        try:
            while True:
                if daq.hw_ver == 'EM08C-RRLL':
                    print("Enter new current (mA): ")
                else:
                    print("Enter new voltage (V): ")
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
    calib = Calib(args.port)
    if test:
        meter = usbtmc.RigolDM3058(args.meter) if args.auto else None
        test = Test(args.port)
        results_dac = test.test_dac(args.meter)
        results_adc = test.test_adc()
        if args.json:
            test.create_test_json(results_adc, results_dac)
    elif args.show:
        logging.info(title("DAC calibration"))
        calib.print_calib(calib.get_dac_calib())
        logging.info(title("ADC calibration"))
        calib.print_calib(calib.get_adc_calib())
    elif args.reset:
        logging.info("Resetting calibration values")
        calib.reset_calib()
    elif args.dac:
        logging.info(title("Calibrating DAC"))
        meter = usbtmc.RigolDM3058(args.meter) if args.auto else None
        calib.calib_dac(args.file, meter)
        if args.json:
            calib.create_calib_json()
    else:
        logging.info("Resetting calibration values")
        calib.reset_calib()
        logging.info(title("Calibrating DAC"))
        meter = usbtmc.RigolDM3058(args.meter) if args.auto else None
        calib.reset_calib()
        calib.calib_dac(args.file, meter)
        calib.calib_adc()
        if args.json:
            calib.create_calib_json()


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
    cparser.add_argument('-r', '--reset', action='store_true',
                         help='Reset calibration values')
    cparser.add_argument('-d', '--dac', action='store_true',
                         help='Apply DAC calibration and exit')
    cparser.add_argument('-f', '--file', default='calib.txt',
                         help='Select file source to load DAC parameters'
                         '(default: calib.txt)')
    cparser.add_argument('-s', '--show', action='store_true',
                         help='Show calibration values')
    cparser.set_defaults(func=calib_cmd)

    # 'test' command parser
    tparser = subparsers.add_parser('test', help='Test device calibration')
    tparser.set_defaults(func=lambda args: calib_cmd(args, True))

    for t in [cparser, tparser]:
        t.add_argument('-j', '--json',
                       help='Generate json file', action='store_true')
        t.add_argument('-a', '--auto', action='store_true',
                       help='Automated testing using a USB multimeter')

    # 'set-voltage' command parser
    vparser = subparsers.add_parser('set-voltage', help='Set DAC voltage')
    vparser.add_argument('-i', '--interactive', action='store_true',
                         help='Interactively ask for voltage values')
    vparser.add_argument('volts', type=float, help='Output voltage')
    vparser.add_argument('-ch', '--channel', type=int, help='Output channel')
    vparser.set_defaults(func=set_voltage_cmd)

    # 'serial' command parser
    sparser = subparsers.add_parser('serial',
                                    help='Read or write the serial number')
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
