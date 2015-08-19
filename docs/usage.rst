***********************
openDAQ usage in Python
***********************

Device connection and port handling
=============================================


To establish a connection with the openDAQ through the command line type the following:


 .. code:: python

  python

  from opendaq import DAQ
  
  a = DAQ("/dev/ttyUSB0")
  
  
When creating an object of type DAQ, you have to specify the actual port at wich the openDAQ is connected. This can be done, in UNIX operating systems, typing in the terminal:

 .. code:: python

 $ dmesg

You should see something like this:

 .. code:: python

  ...
  ...
  ...
  for cp210x
  [17755.465949] cp210x 1-4.4:1.0: cp210x converter detected
  [17755.536101] usb 1-4.4: reset full-speed USB device number 5 using ehci-pci
  [17755.629330] usb 1-4.4: cp210x converter now attached to ttyUSB0

In this example, openDAQ is attached to the USB port named ttyUSB0. 

If you are working in Windows, the name of the port will be like "COMxx" instead of "/dev/ttyUSBxx". You can check the port in Control Panel->System->Device Manager.

Now, with the object a created, we can start working with it. If you want to close the port, simply type the following:

 .. code:: python

  a.close()


ADC reading (Command-Response mode)
===================================

First of all, we must configure the ADC,specifying the positive analog input, and the negative analog input if we want to do differential measures. 

This can be done using the *conf_adc* function:

 .. code:: python

  a.conf_adc(pinput,ninput,gain,nsamples)


The values of these parameters are listed in the following table:




===========     ======================= =============== =====================
Parameter            Description             Value       Notes
===========     ======================= =============== =====================
pinput           Positive input          1:8             AN1-AN8

ninput           Negative input          M:0,5,6,7,8,25  0: ref ground
                                         
                                         S: 0, 1:8       25: ref 2,5 V ; rest: input pins
                                         
                                         
gain             Analog gain             M: 0:4          x1/3,x1,x2,x10,x100

                                         S: 0:7          x1,x2,x4,x5,x8,x10,x20

nsamples         Number of samples per   [0-254]
                 data point     
===========     ======================= =============== =====================



There are three options to read the ADC. 

If we want the raw data from the ADC, we can use 

 .. code:: python

  data = a.read_adc()

  print data

  
Much better, if we want the data directly in Volts, just use:

 .. code:: python

  data_Volts = a.read_analog()

Finally, we also can read all the analog inputs simultaneously using the function *read_all*:

 .. code:: python

  data_Volts = a.read_all()

This function return a list with the lectures (in Volts) of each channel.

DAC setting (CR mode)
==============================

As in the case of reading the ADC, there are two functions to set the output of the DAC: *set_analog('V')* and *set_dac('raw')*. The first set DAC output voltage in V betwen the voltage hardware limits :

 .. code:: python

  a.set_analog(1.5)



The function *set_dac* set the DAC with the raw binary data value:


 .. code:: python

  a.set_dac(3200)



===========     ======================= 
Model           Output Voltage Range     
===========     ======================= 
openDAQ[M]         [-4,096V  4,096V]          

openDAQ[S]        [0V 4,096V]          
                                         
===========     =======================                                          
                                         

Stream Experiments Creation (Stream Mode)
==============================================

OpenDAQ has two main modes of operation: Command-Response Mode and Stream (hardware-timed) Mode. 

In command-response mode all communications are initiated by a command from the host PC, wich is followed by a response from openDAQ. 

On the other hand, the Stream mode is a continous hardware-timed input mode where a list of channels that are scanned at a specified rate.

Stream Mode can be used in three kind of experiment modes, wich differ in the maximum scan rate allowed and the source of the timing clock (internal or external). We define an experiment as a certain data source with specific configuration, sampling rate and start and stop conditions:

- Stream experiments
- External experiments
- Burst experiments

Once the experiment is configured we can start it:

 .. code:: python

  a.start()

or stop it:

 .. code:: python

  a.stop()
  
We can read the data using the method *read*:

 .. code:: python

  stream_exp.read()


Stream experiments
------------------

For Stream Experiments, a specific data source is sampled in regular intervals, using internal timer to keep time count (Timer2). Fastest scan rate in this mode is 1kSPS (1ms of period).

User can configure up to 4 Stream experiments to be running simultaneously. They will have each an
internal buffer of about 400 samples, which will be normally enough not to lose any point in the
communications.

First of all we have to import the library and the constant definitions:

 .. code:: python

  from opendaq import *
  from opendaq.daq import *

To create an Stream Experiment use the following function:


 .. code:: python

  stream_exp = a.create_stream(mode,period,npoints,continuous,buffersize)

with parameters:


===========     ======================= =============== =====================
Parameter            Description             Value       Notes
===========     ======================= =============== =====================
mode              Define data source        0:5           0:ANALOG_INPUT
                  or destination                          1:ANALOG_OUTPUT
                                                          2:DIGITAL_INPUT
                                                          3:DIGITAL_OUTPUT
                                                          4:COUNTER_INPUT
                                                          5:CAPTURE_INPUT
period            Period of the stream      1:65536                    
                  experiment                                  

npoints           Total number of           0:65536       0 indicates continous adquisition (By default 10)
                  points for the 
                  experiment 

continuous        Indicates if           True or False   False:run once (By default False)
                  experiment is 
                  continuous
                                         
buffersize        Buffer size                           By default 1000 (optional)
                                         
                                         

===========     ======================= =============== =====================


Once created the experiment we can configure the input to read. For example, if we want to read the analog input 6 (AN6), without gain, we should use:

 .. code:: python

  stream_exp = a.create_stream(ANALOG_INPUT,200,continuous=False)

Now, we have to configure the channel. To do this we use the method *analog_setup* of the class *DAQStream*:

 .. code:: python

  stream_exp .analog_setup(pinput,ninput,gain,nsamples)

with parameters:

===========     ======================= =================  =============
Parameter            Description             Value            Notes
===========     ======================= =================  =============
pinput             Positive/SE analog         1:8                           
                   input         

ninput             Select negative        M:0,5,6,7,8,25
                   analog input           S:0,1:8 
                                         
  gain           Select PGA multiplier  M: 0:4             x1/2,x1,x2,x10,x100
                                                           x1,x2,x3,x4,
                                        S: 0:7             x8,x10,x16,
                                                           x20                          
nsamples         Number of samples to    0:255
                 calculate the mean 
                 for each point       
===========     ======================= =================  =============

For the example above:

 .. code:: python

  stream_exp .analog_setup(pinput=7,gain=GAIN_S_X2)


External experiments
---------------------

External experiments use an external digital trigger source to perform readings. Fastest scan rates are in similar ranges as for the Stream experiments. The rest of properties and parameters are similar to Stream experiments.

User can define up to 4 external experiments at the same time, each of one connected to digital inputs D1 to D4 (the number of the internal DataChannel is connected to the digital input number) to act as trigger inputs.

Maximum number of experiments will be 4 in total, including all External and Stream experiments.

To create an External Experiment use the following function:


 .. code:: python

  a.create_external(mode,clock_input,edge,npoints,continuous,buffersize)

The new parameters here are *clock_input* and *edge*, which are explained in the following table:



===========     ======================= =============== =====================
Parameter            Description             Value       Notes
===========     ======================= =============== =====================
clock_input       Assign a DataChannel    1:4
                  number and a digital
                  input for this 
                  experiment                    

edge             New data on rising (1)      0:1           
                 or falling (0) edges                                 
                                         
                                         
                                         

===========     ======================= =============== =====================


For example, we are going to create an external experiment with an analog readin in AN8 (SE):

 .. code:: python

  extern_exp = a.create_external(ANALOG_INPUT,1,edge=1,npoints=10,continuous=False,buffersize=1000)



As with the stream experiment, now we have to setup the analog input:


 .. code:: python

  stream_exp.analog_setup(pinput=8,gain=GAIN_S_X1,nsamples=20)
  
  a.start() 

We can use a while loop in this way:

 .. code:: python

  while a.is_measuring():
      print "data", extern_exp.read()


Burst experiments
---------------------

Burst experiments are also internally timed, like Stream experiments, but they are intended to use a faster sampling rate, up to 10kSPS. 
The high acquisition rate limits the amount of things that the processor is capable of doing at the same time. 
Thus, when a Burst experiment is carried out, no more experiments can run at the same time.

Burst experiment use a bigger internal buffer of about 1600 points to temporary store results. However, if the experiment goes on for a long time, the buffer will eventually get full and the firmware will enter “Auto-recovery” mode. This means that it will get no more points until buffer gets empty again, having
an time where no sample will be taken.

To create a burst experiment use the following function:

 .. code:: python

  burst_exp = a.create_burst(mode,period,npoints,continuous)


Here is an example of a how a burst experiment is configured to do a analog output streaming:

 .. code:: python

  preload_buffer = [0.3, 1, 3.3, 2]
  burst_source = a.create_burst(mode=ANALOG_OUTPUT, period=200, npoints=len(preload_buffer), continous=False)
  burst_source.analog_setup()
  burst_source.load_signal(preload_buffer)

  a.start()


Analog output streaming 
-----------------------

With Stream and Burst experiments we can load  a generic waveform (of any type) and the device will reproduce it through the DAC. This can be achieved by this way:
 
 -First create the waveform:
 
    .. code:: python

       preload_buffer = [0.3, 1, 3.3, 2] # The waveform
   
 -Next, create the experiment (Stream or Burst, see next subsections)

 -Finally load the signal to the experiment:

    .. code:: python

       exp_name.load_signal(preload_buffer)


IMPORTANT NOTE: Analog output streams always use internal DataChannel #4, thus digital input D4 will not be available for an External experiment.


Capture Input
==============================================

The capture input permits measuring the time length of incoming digital signals.
It makes use of device internal timer to calculate the time elapsed between changes in state (high to low or low to high) of an external signal. OpenDAQ has a main clock running at 16MHz, which limits the minimum periods that the device is able to measure to several microseconds.

The input in this mode is D5 (DIO 5 pin)

There are three methods associated with this mode: *init_capture*, *stop_capture* and  *get_capture*. To start measuring use 

 .. code:: python

  a.init_capture(period)

where period is the estimated period of the wave (in microseconds), and its range is [0,65535]. Now , we can get the Capture reading:

 .. code:: python

  a.get_capture(mode)

where 

===========     ==============          ========================
Parameter            Value               Notes    
===========     ==============          ========================
mode             0:3                     0: Low cycle
                                         
                                         1: High cycle

                                         2: Full period

===========     ==============          ======================== 

Finally, stop the capture when the experiment has finished:

 .. code:: python

  a.stop_capture(mode)

Counter Input
==============================================

The counter input is also based on Timer 1, and its functionality consists on counting number of edges coming through the port (D6). This can be useful to measure the frequency of very fast signal or to read some kind of sensors.


User can select which kind of digital edges will the peripheral detect (high or low), and he can also read and reset the counter back to 0 whenever it is necessary.

Maximum number of edges is 65535 (16 bit counter).

To start counting type the following:

 .. code:: python

  a.init_counter(edge)

This method configure which edge increments the count: Low-to-High (1) or High-to-Low (0). To get the counter value:

 .. code:: python

  a.get_counter(reset)

If *reset>0* , the counter is reset after perform the reading.



Encoder Input
==============================================

The encoder input is based on external interrupts on pin D6. Its functionality consists on counting number of edges coming through the digital input D6 while keeping track of the direction of the movement, by reading D5 on each interrupt.


User can select the maximum resolution of the encoder.

To work in this mode there are three methods. The first start the encoder function:

 .. code:: python

  a.init_encoder(resolution)

Resolution is the maximum number of ticks per round ([0:65535]).This command configures external interrupts on D6 and resets the pulse counter to 0. Next, to get the current encoder relative position use:

 .. code:: python

  a.get_encoder()

This method returns the actual encoder value. Finally, stop the encoder:

 .. code:: python

  a.stop_encoder()


PWM Output
==============================================

Pulse Width Modulator generates a continuous digital signal at a given frequency. Duty refers to the portion of time that the signal spends in High state.

PWM output is connected to port D6 of openDAQ.

To start the PWM Output mode use the following method:


 .. code:: python

  a.init_pwm(duty,period)

Duty is the high time of the signal ([0:1023]). If 0, the signal is always low. Period is the period of the signal in microseconds. To stop the PWM:

 .. code:: python

  a.stop_pwm()



PIO COnfiguration and control (CR mode)
==============================================

The openDAQ has 6 DIO (digital Inputs/Outputs). We have 4 DIO lines on the right side screw terminal block (D1-D4), and the two others on the left terminal block (D5-D6).

D5 is a multipurpose terminal that is connected with internal microprocessor’s Timer/Counter 2. Apart from being used as a DIO, this terminal can be configured as PWM output, Counter input or Capture input.
 
All the digital I/O lines include an internal series resistor and a protective diode that provides overvoltage/short-circuit protection. The series resistors (about 100Ω) also limit the ability of these lines to sink or source current.


The DIOs have 3 possible states: input, output-high, or output-low. Each line of I/O can be configured individually. When configured as an input, the line has a 50kΩ pull-up resistor to 5.0 volts. When configured as output-high, the line is connected to the internal 5.0 volt supply (through a series resistor).
When configured as output-low, a bit is connected to GND (through a series resistor). All digital I/O are configured to be inputs at power up.

 
We have two couples of commands to control the digital I/O lines. The first two ones control each line individually, one to set or read the line direction (input or output), and the other to read or set the line value (high or low). The other two commands control the six lines at a time, one function to read or set the lines direction, and the other command to read or set the lines values.



==============      ======================= ===========================
Method                  Arguments                       Notes
==============      ======================= ===========================
*set_pio_dir*        number: 1:6              PIO number                        

                     output: 0:1              0: input; 1: output

*set_pio*            number: 1:6              PIO number                

                     value: 0:1               Digital value: 0 Low, 1 High

*set_port_dir*       output: 0:1              0: input; 1: output                       

                    

*set_port*          value: 0:1               Digital value: 0 Low, 1 High 

                     
==============      ======================= ===========================

Bit-bang SPI Output
==============================================



The Serial Peripheral Interface (SPI) is a very popular communications bus, used widely in electronics to control slave devices. This utility allows openDAQ to communicate with other low level devices, like external port expanders, PGAs, switches or other peripherals.


SPI is a synchronous serial data link that operates in full duplex mode, using a master/slave scheme, where the master device always initiates the data frame. Multiple slave devices are allowed with separated select lines.


The SPI bus specifies four logic signals:

- SCLK: serial clock (output from master)
- MOSI: master output, slave input (output from master)
- MISO: master input, slave output (output from slave)
- SS: slave select (active low, output from master)

To begin a communication, the bus master first configures the clock, and then transmits the logic 0 for the desired chip over the chip select line (SS). During each SPI clock cycle, a full duplex data transmission
occurs:

- The master sends a bit on the MOSI line, and the slave reads it from that same line
- The slave sends a bit on the MISO line, and the master reads it from that same line

Transmissions may involve any number of clock cycles.


A relevant issue concerning SPI transmissions, is how the SCLK behaves, and when the MISO and MOSI lines should be read. By convention, these options are named CPOL (clock polarity) and CPHA (clock phase). At CPOL=0 the base value of the clock, when inactive, is zero. CPHA=0 means sample on the leading (first) clock edge, while CPHA=1 means sample on the trailing (second) clock edge, regardless of whether that clock edge is rising or falling. Taking this into consideration, we can define up to four SPI modes, by combining the two possible values of each option.

OpenDAQ uses a so called bit-bang SPI mode, as the bus signals are generated entirely by software (no specific hardware is used).

Specific commands are available to configure the functions of the pins (which DIO number will be used for each SPI line) and the SPI mode (CPOL and CPHA). The SS lines must be controlled separately, using any of the DIO terminals not configured as SPI line (PIO command must be used).

To configure Bit-bang SPI use this method:

 .. code:: python

  a.spi_config(cpol,cpha)

Here, *cpol* is the clock polarity (clock pin state when inactive) and *chpa* is the clock phase (leading 0, or trailing 1 edges read).

To select the PIO numbers to use, we have  the following method:


 .. code:: python

  a.spi_setup(nbytes,sck,mosi,miso)

where 

===========     ==============          ========================
Parameter            Value               Notes    
===========     ==============          ========================
nbytes                                    Number of bytes

sck             1 by default                   Clock pin

mosi             2 by default                  MOSI pin

miso             3 by default                  MISO pin       
                                         


===========     ==============          ======================== 

Finally, to transfer (send and receive) a byte or a word use:


 .. code:: python

  a.spi_write(value,word)

If *word = True* , then we are sending a 2-byte word instead of a byte.



Other functions
==============================================
There are other methods that can be used with the openDAQ. They are listed below:



==============      ================= =========================================
Method                  Arguments                       Notes
==============      ================= =========================================
*enable_crc*         on               Enable/Disable the cyclic redundancy check                     



*set_led*           color              0:off ; 1: green ; 2: red ; 3: orange                



*set_id*            id:  [000:999]            Identify openDAQ device
                    

*device_info*               None         Read device configuration:

                                           Hardware version
                         
                                           Firmware version

                                           Device ID number

                     
==============      ================= =========================================



Calibration
==============================================


AIN and DAC commands are transmitted between the host PC and the device with the raw binary values used in the internal transmission with the peripherals. For example, ADC values range in the openDAQ [M] from 0 to 65535 and DAC values from 0 to 8191. These numbers must be operated in order to get the actual value, in millivolts, that is being read through
the ADC or to convert a desired output value in millivolts to become the actual voltage for the DAC output. For these calculations to be done, a good approximation is to suppose that the actual values are linear functions of the raw values.

In case of openDAQ-[M] the raw values of the ADC inputs are function of the gain selected, so we will have a different calibration line for each gain setting. On the other hand, we can suppose that all the inputs A1-A8 share the same calibration line, as the signals are multiplexed and then go through the same analog circuitry.

In case of openDAQ-[S] the raw values that the ADC returns, are function of the analog input selected, because each resistor bridge will have its own tolerance deviations. Then, we will have a different calibration line for each input setting: one for each analog input configured as SE reading, and another one for each input in DE mode. On the other hand, we can suppose that all the PGA values share the same calibration line. This is because they are applied inside the ADC converter, and the ADS7871 internal PGA values are very well fitted.

The functions that manage the calibration are:

-  .. code:: python

       a.set_cal(gains,offsets,flags)

  This method set the device calibration. Gains and offsets are the values of calibration for each configuration, i.e, they are lists of values. The readings of the analog inputs are bynary values, so we have to transform them to Volts. This is achieved using the formula 

   :math:`V =  (gains*bits)+offset`. 

  If the device is an openDAQ [M], the gains and offsets  are multiplied by 100000  to pack  the  floating  value  into  a  16bit  integer  to  be  stored  in  the EEPROM.

  If the device is an openDAQ [S], the gains and offsets are multiplied by 10000  to pack  the  floating  value  into  a  16bit  integer  to  be  stored  in  the EEPROM. 

  The argument *flags* indicates if the device is an openDAQ [M] ('M'), or if it is an openDAQ [S] ('SE' and 'DE') in which case we have to calibrate in SE and DE modes.

-  .. code:: python

       a.get_cal()

  This method gets calibration values for all the available device configurations. It returns the *gains* and *offsets* lists.

-  .. code:: python

       a.set_dac_cal(gain,offset)

  This method is similar to *set_cal* method, and it set DAC calibration values. Here, *gain* and *offset* are numbers, not lists as in *set_cal* method.

-  .. code:: python

       a.get_dac_cal()

  Returns DAC gain and offset.


