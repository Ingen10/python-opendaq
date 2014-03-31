:Authors:
 JRB, MF
:Version:
 1.0
:Date:
 05/12/2013

==========================
DAQ.PY FUNCTION REFERENCE:
==========================

**crc(data):**
===============

Create cyclic redundancy check.

**check_crc(data):**
====================

Cyclic redundancy check.

*Args:*
    + data: variable that saves the checksum.
*Raises:*
    + CRCError: Checksum incorrect.

check_stream_crc(head, data):
=============================

Cyclic redundancy check for streaming.

*Args:*
    + head: variable that defines the header.
    + data: variable that defines the data.


open():
===========

Open serial port.

Configure serial port to be opened.

close():
============

Close serial port.

Configure serial port to be closed.

send_command(cmd, ret_fmt, debug):
==============================================

Build a command packet, send it to the openDAQ and process the response

        * Args:
            + cmd: Command ID
            + ret_fmt: Payload format using python 'struct' format characters
            + debug: Toggle debug mode ON/OFF
        * Returns:
            + Command ID and arguments of the response
        * Raises:
            + LengthError: The legth of the response is not the expected

get_info():
===============

Read device configuration: serial number, firmware version and hardware version.

*Returns:*
    + Hardware version.
    + Firmware version.
    + Device ID number.

get_vHW():
==============

Get the hardware version.

*Returns:*
    + Hardware version.

read_adc():
===============

Read the analog-to-digital converter.

Read data from ADC and return the 'RAW' value.

*Returns:*
    + ADC value: ADC raw value.

read_analog():
==================

Read the analog data.

ead data from ADC and convert it to millivolts using calibration values.

*Returns:*
    + Analog reading: Analog value converted into millivolts.

conf_adc(pinput, ninput, gain, nsamples):
======================================================

Configure the analog-to-digital converter.

Get the parameters for configure the analog-to-digital
converter.     

* Args:*
    - pinput: Positive input [1:8]
    - ninput: Negative input
        - openDAQ[M]= [0, 5, 6, 7, 8, 25]
        - openDAQ[S]= [0,1:8] (must be 0 or pinput-1)
    - gain: Analog gain
        - openDAQ[M]= [0:4] (x1/3, x1, x2, x10, x100)
        - openDAQ[S]= [0:7] (x1,x2,x4,x5,x8,x10,x16,x20)
    - nsamples: Number of samples per data point (1-255)

*Returns:*
    - ADC value: ADC raw value
    - pinput: Positive input
    - ninput: Negative input
    - gain: Analog gain
    - nsamples: Number of samples per data point


enable_crc(on):
=====================

Enable/Disable cyclic redundancy check.

*Args:*
    - on: Enable CRC
    
set_led(color):
=====================

Choose LED status.

LED switch on (green, red or orange) or switch off.

*Args:*
    - color: variable that defines the led color (0=off,
        1=green,2=red, 3=orange). 
*Raises:*
    - ValueError: Invalid color number 
        
set_analog(volts):
========================

Set DAC output voltage (millivolts value).

Set the output voltage value between the voltage hardware limits.
Device calibration values are used for the calculation.
Range: -4.096V to +4.096V for openDAQ[M]
Range: 0V to +4.096V for openDAQ[S]

*Args:*
    - volts: variable that defines the output value.
*Raises:*
    - ValueError: An error ocurred when voltage is out of range and print 'DAc voltage out of range'.

set_dac(raw):
===================

Set DAC with raw value.

Set the raw value into DAC without data conversion.

*Args:*
    - raw: RAW binary ADC data value.
*Raises:*
    - ValueError: An error ocurred when voltage is out of range and print 'DAC voltage out of range'.

set_port_dir(output):
===========================

Configure all PIOs directions.
Set the direction of all D1-D6 terminals.

*Args:*
    - output: Port directions byte (bits: 0:input, 1:output)

set_port(value):
======================

Write all PIOs values.
Set the value of all D1-D6 terminals.

*Args:*
   - value: Port output value byte (flags: 0 low, 1 high).


set_pio_dir(number, output):
==================================

Configure PIO direction.
Set the direction of a specific PIO terminal (D1-D6).

*Args:*
    - number: PIO number [1:6]
    - output: PIO direction (0 input, 1 output)
*Raises:*
    - ValueError: Invalid PIO number

set_pio(number, value):
=============================

Set PIO output value.
Set the value of the PIO terminal (0: low, 1: high).

*Args:*
    - number: PIO number [1:6]
    - value: digital value (0: low, 1: high)
*Raises:*
    - ValueError: Invalid PIO number
    
init_counter(edge):
=========================

Initialize the edge counter.

Configure which edge increments the count:
Low-to-High (1) or High-to-Low (0).

*Args:*
    - edge: high-to-low (0) or low-to-high (1)
    
get_counter(reset):
=========================

Get the counter value.

*Args:*
    - reset: reset the counter after perform reading

init_capture(period):
===========================

Start capture mode arround a given period.

*Args:*
    - period: estimated period of the wave (in microseconds)

stop_capture():
===================

Stop capture mode.

get_capture(mode):
========================

Get current period length.

Low cycle, High cycle or Full period.

*Args:*
    - mode: variable that defines the period length.
        - 0 Low cycle
        - 1 High cycle
        - 2 Full period
*Returns:*
    - mode: 
    - Period: The period length in microseconds.


init_encoder(resolution):
===============================

Start encoder function.

*Args:*
    - resolution: Maximum number of ticks per round [0:65535]

get_encoder():
==================

Get current encoder relative position.

*Returns:*
    - Position: The actual encoder value. 

init_pwm(duty, period):
=============================

Start PWM whit a given period and duty.

*Args:*
    - duty: High time of the signal [0:1023](0 always low, 1023 always high)
    - period: Period of the signal (microseconds) [0:65535]
    
stop_pwm():
===============

Stop PWM.

__get_calibration(gain_id):
=================================

Read device calibration for a given analog configuration.
Gets calibration gain and offset for the corresponding analog configuration.

*Args:*
    - gain_id: variable that defines the analog configuration.
      (1:6 for openDAQ [M])
      (1:17 for openDAQ [S])
*Returns:*
    - Gain (100000[M] or 10000[S])
    - Offset

get_cal():
==============

Gets calibration values for all the available device configurations.

*Returns:*
    - Gains
    - Offsets

get_dac_cal():
==================

Read DAC calibration.

*Returns:*
    - DAC gain
    - DAC offset

__set_calibration(gain_id, gain, offset):
===============================================

Set device calibration.

*Args:*
    - gain_id: ID of the analog configuration setup
    - gain: Gain multiplied by 100000 ([M]) or 10000 ([S])
    - offset: Offset raw value. [-32768:32768].

set_cal(gains, offsets, flag):
====================================

Set device calibration.

*Args:*
    - gains: Gain multiplied by 100000 ([M]) or 10000 ([S])
    - offsets: Offset raw value (-32768 to 32768)
    - flag: 'M', 'SE' or 'DE'


set_DAC_cal(self, gain, offset):
================================

Set DAC calibration.


conf_channel(number, mode, pinput, ninput, gain, nsamples):
=======================================================================

Configure a channel for a generic stream experiment.
(Stream/External/Burst).

*Args:*
    - number: Select a DataChannel number for this experiment
    - mode: Define data source or destination [0:5]:
        0) ANALOG_INPUT
        1) ANALOG_OUTPUT
        2) DIGITAL_INPUT
        3) DIGITAL_OUTPUT
        4) COUNTER_INPUT
        5) CAPTURE INPUT
        
    - pinput: Select Positive/SE analog input [1:8]
    - ninput: Select Negative analog input:
        * 0= GND
        * 25= 2.5V Vref
        * 5:8= Analog inputs A5-A8   
        
    - gain: Select PGA multiplier. 
        In case of openDAQ [M]:
            0. x1/2
            1. x1
            2. x2
            3. x10
            4. x100    

        In case of openDAQ [S]:
            0. x1
            1. x2
            2. x4
            3. x5
            4. x8
            5. x10
            6. x16
            7. x20    
  
    - nsamples: Number of samples to calculate the mean for each point [1:255].
    
setup_channel(number, npoints, continuous):
======================================================

Configure the experiment's number of points.

*Args:*
    - number: Select a DataChannel number for this experiment
    - npoints: Total number of points for the experiment
            [0:65536] (0 indicates continuous acquisition)
    - continuous: Number of repeats [0:1]
        * 0 continuous
        * 1 run once

destroy_channel(number):
==============================

Delete Datachannel structure.

*Args:*
    - number: Number of DataChannel structure to clear
        [0:4] (0: reset all DataChannels)

create_stream(number, period):
====================================

Create Stream experiment.

*Args:*
    - number: Assign a DataChannel number for this experiment [1:4]
    - period: Period of the stream experiment
        (milliseconds) [1:65536]

create_burst(period):
===========================

Create Burst experiment.

*Args:*
    - period: Period of the burst experiment
        (microseconds) [100:65535]

create_external(number, edge):
====================================

Create External experiment.

*Args*
    - number: Assign a DataChannel number for this experiment [1:4]
    - edge: New data on rising (1) or falling (0) edges [0:1]

load_signal(data, offset):
================================

Load an array of values to preload DAC output.

*Args:*
    - data: Total number of data points [1:400]
    - offset: Offset for each value

start():
============

Start all available experiments

stop():
===========

Stop all running experiments

flush():
============

Flush internal buffers

flush_stream(data, channel):
==================================

Flush stream data from buffer

*Args:*
   - data: 
   - channel: Experiment number

*Returns:*
    - 0 if there is no incoming data.
    - 1 if data stream was processed.
    - 2 if no data stream received. Useful for debugging.

*Raises:*
   - LengthError: An error ocurred.

get_stream(data, channel, callback):
============================================

*Args:*
    - data: Data buffer
    - channel: Experiment number
    - callback: Callback mode

*Returns:*
    - 0 if there is not any incoming data.
    - 1 if data stream was processed.
    - 2 if no data stream received.

set_DAC_gain_offset(g, o):
================================

Set DAC gain and offset.

*Args:*
    - g: DAC gain.
    - o: DAC offset.

set_gains_offsets(g, o):
==============================

Set gains and offsets.

*Args:*
    - g: Gains.
    - o: Offsets.

set_id(id):
=================

Identify openDAQ device.

*Args:*
    - id: id number of the device [000:999].

spi_config(cpol, cpha):
===============================

Bit-Bang SPI configure (clock properties).

*Args:*
    - cpol: Clock polarity (clock pin state when inactive)
    - cpha: Clock phase (leading 0, or trailing 1 edges read)

*Raises:*
    - ValueError: An error ocurred
    
spi_setup(nbytes, sck=1, mosi=2, miso=3):
=======================================================

Bit-Bang SPI setup (PIO numbers to use).

*Args:*
    - nbytes: Number of bytes
    - sck: Clock pin
    - mosi: MOSI pin (master out / slave in)
    - miso: MISO pin (master in / slave out)
*Raises:*
    - ValueError

spi_write(value, word=False):
================================

it-bang SPI transfer (send+receive) a byte or a word.

*Args:*
    - value: Data to send (byte/word to transmit)
    - word: send a 2-byte word, instead of a byte
    


