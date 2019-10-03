import time
import sys

import json
import logging
from terminaltables import AsciiTable

from opendaq.models import InputType, OutputType
from opendaq.calib import Calib

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


class Test(Calib):
    def __init__(self, port):
        Calib.__init__(self, port)

    def create_test_json(self, results_inputs, results_outputs):
        filename = '%s_%s_test.json' % (self.serial_str, time.strftime('%y%m%d'))
        f = open(filename, 'w')
        data = {
            "model": self.hw_ver,
            "serial": self.serial,
            "time": int(time.time()),
            "items": []
        }
        for idx, o in enumerate(results_outputs):
            out = self.get_dac_types(int(o['number']))
            data['items'].append({'dc_range': (out.vmax - out.vmin),
                                  'number': o['number'],
                                  'type': 'current_output',
                                  'unit': o['unit'],
                                  'readings': [
                                                {'dc_ref': o['ref'],
                                                 'dc_read': o['read']
                                                }]})
        for idx, i in enumerate(results_inputs):
            inp = self.get_adc_types(int(i['number']))
            data['items'].append({'dc_range': (inp.vmax - inp.vmin),
                                  'number': i['number'],
                                  'type': 'stat_input',
                                  'unit': i['unit'],
                                  'readings': [
                                                {'dc_ref': it['ref'],
                                                 'dc_read': it['read'],
                                                 'gain': it['gain']
                                                } for it in i['items']]})
        json.dump(data, f, indent=2)
        f.close()

    def __test_adc_Atype(self, pinputs):
        gains = self.get_input_gains(pinputs[0])
        results = [{'number': p, 'items': [], 'unit': 'V'} for p in pinputs]
        set_value_ant = 0
        for p in pinputs:
            self.conf_adc(p, 0, 0)
        time.sleep(.5)
        for idx, g in enumerate(gains):
            if g <= 2:
                set_value = 5.
            elif 2 < g <= 16:
                set_value = 1.
            elif g == 32:
                set_value = 0.5
            if(set_value_ant != set_value):
                while not yes_no("Set %f V at all inputs.\nPress 'y' when ready." % set_value):
                    pass
                set_value_ant = set_value
            time.sleep(.5)
            for j, p in enumerate(pinputs):
                time.sleep(.3)
                self.conf_adc(p, 0, idx)
                results[j]['items'].append({
                                            'gain': g,
                                            'ref': set_value,
                                            'read': self.read_analog()[0]})
        return results

    def __test_adc_shunts(self, pinputs):
        results = [{'number': p, 'items': [], 'unit': 'mA'} for p in pinputs]
        for p in pinputs:
            self.conf_adc(p, 1, 0)
        time.sleep(.5)
        for j, p in enumerate(pinputs):
            gains = self.get_input_gains(p)
            set_value_ant = 0
            for idx, g in enumerate(gains):
                if g <= 16:
                    set_value = 10.0
                elif g == 32:
                    set_value = 5.0
                if (set_value_ant != set_value):
                    set_value_ant = set_value
                    while not yes_no("Set %f mA at input %d.\nPress 'y' when ready.\n" % (set_value, p)):
                        pass
                time.sleep(.3)
                self.conf_adc(p, 1, idx)
                print(self.read_analog()[0])
                results[j]['items'].append({
                                            'gain': g,
                                            'ref': set_value,
                                            'read': self.read_analog()[0]})
        return results

    def __test_adc_AStype(self, pinputs):
        results = self.__test_adc_Atype(pinputs)
        results_s = self.__test_adc_shunts(pinputs)
        results.extend(results_s)
        return results

    def __test_adc_MNtype(self, pinputs, istypeN=True):
        gains = self.get_input_gains(pinputs[0])
        unit = self.get_adc_types(pinputs[0]).unit
        results = [{'number': p, 'items': [], 'unit': unit} for p in pinputs]
        for idx, g in enumerate(gains):
            if istypeN:
                set_value = 2. / g
            else:
                set_value = 1. / g
            self.set_analog(set_value)
            for j, p in enumerate(pinputs):
                self.conf_adc(p, 0, idx)
                results[j]['items'].append({
                                            'gain': g,
                                            'read': self.read_analog()[0],
                                            'ref': set_value})
        return results

    def __test_adc_Ntype(self, pinputs):
        return self.__test_adc_MNtype(pinputs)

    def __test_adc_Mtype(self, pinputs):
        self.__test_adc_MNtype(pinputs, istypeN=False)

    def __test_adc_Stype(self, pinputs):
        set_values = range(5)
        unit = self.get_adc_types(pinputs[0]).unit
        results = [{'number': p, 'items': [], 'unit': unit} for p in pinputs]
        for idx, p in enumerate(pinputs):
            self.conf_adc(p, 0)
            for j, v in enumerate(set_values):
                self.set_analog(v)
                results[j]['items'].append({
                                            'ref': v,
                                            'read': self.read_analog()[0]})
        return results

    def __test_adc(self, inp_type, pinputs):
        print(pinputs)
        if inp_type == InputType.INPUT_TYPE_A:
            results = self.__test_adc_Atype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_AS:
            results = self.__test_adc_AStype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_M:
            results = self.__test_adc_Mtype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_S:
            results = self.__test_adc_Stype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_N:
            results = self.__test_adc_Ntype(pinputs)
        return results

    def test_adc(self):
        results = []
        for t in InputType:
            inputs = []
            for idx, inp in enumerate(self.inputs_ids):
                if (t == inp):
                    inputs.append(idx + 1)
            if inputs:
                results.extend(self.__test_adc(t, inputs))
        return results

    def __test_dac_Ltype(self, outputs):
        current = 10.0
        unit = self.get_dac_types(outputs[0]).unit
        results = [{'number': 0, 'ref': 0, 'read': 0, 'unit': unit} for i in range(len(outputs))]
        for idx, o in enumerate(outputs):
            while not yes_no("Connect the analog output %d to the power and press 'y' when ready.\n" % o):
                pass
            r = self.set_analog(current, o)
            while not(r):
                while not yes_no("Powering error. Connect AOUT%d to the power and press 'y' when ready.\n" % o):
                    pass
                r = self.set_analog(current, o)
            results[idx]['number'] = o
            results[idx]['ref'] = current
            results[idx]['read'] = float(raw_input("Enter the measured value (mA): "))
        return results

    def __test_dac_SNM(self, outputs):
        vmin = self.get_adc_types(0).vmin
        vmax = self.get_adc_types(0).vmax
        volts = range(int(vmin), int(vmax), 2)
        unit = self.get_dac_types(outputs[0]).unit
        results = [{'number': 1, 'ref': 0, 'read': 0, 'unit': unit} for i in range(len(volts))]
        for idx, v in enumerate(volts):
            self.set_analog(v)
            time.sleep(.5)
            results[idx]['ref'] = v
            results[idx]['read'] = raw_input("Enter the measured value: ")
        return results

    def __test_dac_opendaq_auto(self, outputs, meter):
        vmin = self.get_adc_types(0).vmin
        vmax = self.get_adc_types(0).vmax
        volts = range(int(vmin), int(vmax))
        set_values, read_values = self.measure_dac(volts, meter)
        unit = self.get_dac_types(outputs[0]).unit
        results = [{'number': 1, 'ref': 0, 'read': 0, 'unit': unit} for i in range(len(volts))]
        for idx in range(len(volts)):
            results[idx]['ref'] = set_values[idx]
            results[idx]['read'] = read_values[idx]
        return results

    def __test_dac(self, out_type, outputs, meter):
        if out_type in [OutputType.OUTPUT_TYPE_M, OutputType.OUTPUT_TYPE_S]:
            if meter:
                results = self.__test_dac_opendaq_auto(outputs, meter)
            else:
                results = self.__test_dac_SNM(outputs)
        elif out_type == OutputType.OUTPUT_TYPE_L:
            results = self.__test_dac_Ltype(outputs)
        return results

    def test_dac(self, meter):
        for t in OutputType:
            outputs = []
        results = []
        for idx, out in enumerate(self.outputs_ids):
            if(t == out):
                outputs.append(idx + 1)
        if outputs:
            results.extend(self.__test_dac(t, outputs, meter))
        return results

    def print_calib(self, calib):
        rows = [['Gain', 'Offset']]
        for c in calib:
            rows.append(['%.4f' % c.gain, '%.4f' % c.offset])
        print(AsciiTable(rows).table)
