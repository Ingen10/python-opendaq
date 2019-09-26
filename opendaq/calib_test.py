import argparse

from opendaq.calib import Calib
from opendaq.test import Test


def test_cmd(args):
    test = Test(args.port)
    test.test_dac(args.meter)
    test.test_adc()


def calib_cmd(args):
    calib = Calib(args.port)
    calib.reset_calib()
    calib.calib_dac(args.file, args.meter)
    calib.calib_adc()
    if args.report:
        calib.create_calib_json()


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
    cparser.add_argument('-r', '--report', action='store_true',
                         help='Generate json file')
    cparser.set_defaults(func=calib_cmd)

    tparser = subparsers.add_parser('test', help='Test device calibration')
    tparser.add_argument('-r', '--report', action='store_true',
                         help='Generate json file')
    tparser.set_defaults(func=test_cmd)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
