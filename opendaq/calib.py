import time
import numpy as np
import sys

import logging
import json
from terminaltables import AsciiTable

from .daq import DAQ
from .models import InputType, OutputType
from .daq_model import CalibReg

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


class Calib(DAQ):
    def __init__(self, port):
        DAQ.__init__(self, port)
        self.outputs_ids = [self.get_dac_types(i)._output_id
                            for i in range(1, len(self.get_dac_types()) + 1)]
        self.inputs_ids = [self.get_adc_types(i)._input_id
                           for i in range(1, len(self.get_adc_types()) + 1)]

        self.serial = self.get_info()[2]

        self.adc_slots, self.dac_slots = self.get_slots()

    def read_analog_value(self):
        """Read data from ADC in volts.
        :returns: Voltage value.
        """
        self.read_adc()
        time.sleep(0.05)
        return DAQ.read_analog(self)[0]

    def measure_dac(self, values, meter):
        y = []
        for v in values:
            self.set_analog(v)
            time.sleep(0.1)
            y.append(meter.measure('volt_dc'))
        return values, y

    def reset_calib(self):
        adc_calib = self.get_adc_calib()
        dac_calib = self.get_dac_calib()
        self.set_adc_calib([CalibReg(1., 0.)]*len(adc_calib))
        self.set_dac_calib([CalibReg(1., 0.)]*len(dac_calib))

    def create_calib_json(self):
        calib_dac_params = self.get_dac_calib()
        calib_adc_params = self.get_adc_calib()
        filename = '%s_%s_calib.json' % (self.serial_str,
                                         time.strftime('%y%m%d'))
        f = open(filename, 'w')
        data = {
            "model": self.hw_ver,
            "serial": self.serial,
            "time": int(time.time()),
            "inputs": [],
            "outputs": []
        }
        data['humidity'] = int(raw_input('Enter humidity (%): '))
        data['temperature'] = float(raw_input('Enter temperature: '))
        for idx, i in enumerate(self.inputs_ids):
            pos = len(self.inputs_ids) + idx
            data['inputs'].append({'dc_gain': calib_adc_params[idx].gain,
                                   'offset1': calib_adc_params[idx].offset,
                                   'offset2': calib_adc_params[pos].offset
                                   })
            if i == InputType.INPUT_TYPE_M:
                pos = len(self.inputs_ids) + idx
                data['inputs'][idx]['dc_gain2'] = calib_adc_params[pos].gain
            if i == InputType.INPUT_TYPE_AS:
                pos = 2*len(self.inputs_ids) + idx
                data['inputs'][idx]['dc_gain3'] = calib_adc_params[pos].gain
                data['inputs'][idx]['offset3'] = calib_adc_params[pos].offset
        for idx in enumerate(self.outputs_ids):
            data['outputs'].append({'gain': calib_dac_params[idx].gain,
                                    'offset': calib_dac_params[idx].offset})
        json.dump(data, f, indent=2)
        f.close()

    def __calib_adc_ANtype(self, pinputs, isAtype=True):
        calib = self.get_adc_calib()
        volts = 0.0
        if (isAtype):
            while not yes_no("Set %dV at all inputs.\nPress 'y' when ready.\n" % volts):
                pass
        else:
            self.set_analog(volts)
        for p in pinputs:
            print("Calibrating offset of input ", p)
            gains = self.get_input_gains(p)
            raw_read = np.zeros(len(gains))
            for idx, _ in enumerate(gains):
                self.conf_adc(p, 0, idx)
                time.sleep(1)
                raw_read[idx] = self.read_adc()
            corr_gain, corr_offset = np.polyfit(gains, raw_read, 1)
            calib[p - 1] = CalibReg(calib[p - 1].gain, corr_offset)
            pos = len(self.inputs_ids) + p - 1
            calib[pos] = CalibReg(calib[pos].gain, corr_gain)
        self.set_adc_calib(calib)
        if (isAtype):
            volts = 6.0
            while not yes_no("Set %dV at all inputs.\nPress 'y' when ready.\n" % volts):
                pass
        else:
            volts = 2.0
            self.set_analog(volts)
        for p in pinputs:
            self.conf_adc(p, 0, 0)
        time.sleep(.5)
        for p in pinputs:
            self.conf_adc(p, 0, 0)
            time.sleep(.3)
            print(self.read_analog_value())
            calib[p - 1] = CalibReg((self.read_analog_value()/volts),
                                    calib[p - 1].offset)
        return calib

    def __calib_adc_Atype(self, pinputs):
        print("A-TYPE INPUTS")
        print(pinputs)
        return self.__calib_adc_ANtype(pinputs)

    def __calib_adc_Ntype(self, pinputs):
        # Igual que A
        print("N-TYPE INPUTS")
        print(pinputs)
        return self.__calib_adc_ANtype(pinputs, isAtype=False)

    def __calib_ads_shunts(self, pinputs):
        n_measures = 20
        calib = self.get_adc_calib()
        for j, p in enumerate(pinputs):
            while not yes_no("Set 0 mA at input %d.\nPress 'y' when ready.\n" % p):
                pass
            gains = self.get_input_gains(p)
            raw_read = np.zeros(len(gains))
            for idx, _ in enumerate(gains):
                self.conf_adc(p, 1, idx)
                suma = 0
                for _ in range(n_measures):
                    time.sleep(0.01)
                    suma += self.read_adc()
                raw_read[idx] = suma / n_measures
            _, corr_offset = np.polyfit(gains, raw_read, 1)
            pos = 2 * len(pinputs) + j
            calib[pos] = CalibReg(calib[pos].gain, corr_offset)
        self.set_adc_calib(calib)
        for p in pinputs:
            self.conf_adc(p, 1, 0)
        time.sleep(.5)
        current = 15.0
        for idx, p in enumerate(pinputs):
            self.conf_adc(p, 1, 0)
            time.sleep(.3)
            while not yes_no("Set %f mA at input %d.\nPress 'y' when ready.\n" % (current,
                                                                                  p)):
                pass
            suma = 0.0
            for _ in range(n_measures):
                time.sleep(0.01)
                suma += self.read_analog()[0]
                print(self.read_analog()[0])
            pos = 2 * len(pinputs) + idx
            calib[pos] = CalibReg(((suma/float(n_measures))/current), calib[pos].offset)
        return calib

    def __calib_adc_AStype(self, pinputs):
        print("CALIB V")
        print(pinputs)
        calib = self.__calib_adc_Atype(pinputs)
        self.set_adc_calib(calib)
        print("CALIB SHUNTS")
        calib = self.__calib_ads_shunts(pinputs)
        return calib

    def __calib_adc_Mtype(self, pinputs):
        calib = self.get_adc_calib()
        print("M-TYPE INPUTS")
        print(pinputs)
        volts = 0.0
        self.set_analog(volts)
        for j, p in enumerate(pinputs):
            gains = self.get_input_gains(p)
            raw_read = np.zeros(len(gains))
            corr_gain = np.zeros(len(gains))
            for idx, _ in enumerate(gains):
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
                read_value[j] = self.read_analog_value() / volts
            pos = len(self.inputs_ids) + i + 1
            calib[pos] = CalibReg(np.mean(read_value), calib[idx].offset)
        return calib

    def __calib_adc_Stype(self, pinputs):
        calib = self.get_adc_calib()
        print("S-TYPE INPUTS")
        print(pinputs)
        volts = [1., 2., 3., 4.]
        for p in pinputs:
            self.conf_adc(p, 0)
            time.sleep(.3)
            read_raw = np.zeros(len(volts))
            read_analog = np.zeros(len(volts))
            for idx, v in enumerate(volts):
                self.set_analog(v)
                read_analog[idx] = self.read_analog_value()
                read_raw[idx] = self.read_adc()
            new_corr,  new_offset = np.polyfit(volts, read_analog, 1)
            calib[p - 1] = CalibReg(new_corr, new_offset)
        self.set_analog(0)
        ninputs = [2, 1, 4, 3, 6, 5, 8, 7]
        for i, p in enumerate(pinputs):
            self.conf_adc(p, ninputs[i])
            time.sleep(.3)
            pos = len(self.inputs_ids) + i
            calib[idx] = CalibReg(calib[pos].gain, self.read_adc())
        return calib

    def __calib_adc_Ptype(self, pinputs):
        calib = self.get_adc_calib()
        print("P-TYPE INPUTS")
        print(pinputs)
        set_values = [100, 200]
        read_values = np.zeros(len(set_values))
        for p in pinputs:
            self.conf_adc(p)
            for i, v in enumerate(set_values):
                while not yes_no("Set %d ohms at input %d and press 'y' when ready.\n" % (v, p)):
                    pass
                read_values[i] = self.read_analog()[0]
                print(read_values[i])
            gain, offset = np.polyfit(set_values, read_values, 1)
            print(gain, offset)
            calib[p - 1] = CalibReg(gain, offset)
        return calib

    def __calib_adc(self, inp_type, pinputs):
        print("CALIB_IN_ADC")
        if inp_type == InputType.INPUT_TYPE_A:
            calib_out = self.__calib_adc_Atype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_AS:
            calib_out = self.__calib_adc_AStype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_M:
            calib_out = self.__calib_adc_Mtype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_S:
            calib_out = self.__calib_adc_Stype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_N:
            calib_out = self.__calib_adc_Ntype(pinputs)
        elif inp_type == InputType.INPUT_TYPE_P:
            calib_out = self.__calib_adc_Ptype(pinputs)
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
        calib = self.get_dac_calib()
        print("L-TYPE OUTPUTS")
        print(outputs)
        current_values = [5, 20]
        for idx, o in enumerate(outputs):
            read_values = np.zeros(len(current_values))
            for j, c in enumerate(current_values):
                logging.info("Target: %d mA", c)
                while not yes_no("Connect the AOUT%d to the power and press 'y' when ready.\n" % o):
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

    def __calib_dac_from_file(self, outputs, dac_file):
        calib = self.get_dac_calib()
        for idx, _ in enumerate(outputs):
            set_values = []
            read_values = []
            for row in np.loadtxt(dac_file):
                set_values.append(row[0])
                read_values.append(row[idx + 1])
            gain, offset = np.polyfit(set_values, read_values, 1)
            calib[idx] = CalibReg(gain, offset)
        return calib

    def __calib_auto_dac(self, outputs, meter):
        out_type = self.get_dac_types(0)
        volts = range(out_type.vmin, out_type.vmax + 1)
        x, y = self.measure_dac(volts, meter)
        gain, offset = np.polyfit(x, y, 1)
        calib = self.get_dac_calib()[0]
        new_calib = CalibReg(calib.gain*gain, calib.offset + offset)
        return new_calib

    def __calib_dac(self, out_type, outputs, dac_file, meter):
        calib = self.get_dac_calib()
        print("CALIB_IN_DAC")
        self.print_calib(calib)
        if out_type in [OutputType.OUTPUT_TYPE_M, OutputType.OUTPUT_TYPE_S,
                        OutputType.OUTPUT_TYPE_T]:
            if meter and out_type in [OutputType.OUTPUT_TYPE_M,
                                      OutputType.OUTPUT_TYPE_S]:
                calib_out = self.__calib_auto_dac(outputs, meter)
            else:
                calib_out = self.__calib_dac_from_file(outputs, dac_file)
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

    def print_calib(self, calib):
        rows = [['Gain', 'Offset']]
        for c in calib:
            rows.append(['%.4f' % c.gain, '%.4f' % c.offset])
        print(AsciiTable(rows).table)
