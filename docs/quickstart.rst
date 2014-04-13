Quick start
===========

Import the module and connect to the device::

    $ import opendaq
    $ daq = DAQ("ttyUSB0")

Command-Response Mode:
^^^^^^^^^^^^^^^^^^^^^^

Set an output voltage (CR Mode)::

    $ daq.set_analog(0.91)

Configure an analog input and read back the voltage::

    $ daq.conf_adc(8,0,1,20)
    $ daq.read_analog()


Stream Mode:
^^^^^^^^^^^^

Create a new Experiment, Stream type, with a 100ms period, associated to DataChannel #1::

    $ daq.create_stream(1, 100)

Configure the experiment to be an analog reading (A8 as SE input, gain x1)::

    $ daq.conf_channel(1, 0, 8, 0, 1)

<<<<<<< HEAD
Set up the experiment to run continuously::

    $ daq.setup_channel(1, 0)

Create an empty array to store the data, and start the experiment::
=======
Set up the experiment to run continuously:

    $ daq.setup_channel(1, 0)

Create an empty array to store the data, and start the experiment:
>>>>>>> dbfad31e4e07ff381b14b76c62922c954ba594fb

    $ data = []
    $ daq.start()

<<<<<<< HEAD
Keep receiving measured data until you want to stop it::
=======
Keep receiving measured data until you want to stop it:
>>>>>>> dbfad31e4e07ff381b14b76c62922c954ba594fb

    $ daq.get_stream(data)