#!/usr/bin/env python

# Copyright 2015
# Ingen10 Ingenieria SL
#
# This file is part of opendaq.
#
# opendaq is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# opendaq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with opendaq.  If not, see <http://www.gnu.org/licenses/>.

from enum import IntEnum
from collections import deque
from threading import Lock


class ExpMode(IntEnum):
    """Valid experiment modes."""
    ANALOG_IN = 0
    ANALOG_OUT = 1
    DIGITAL_IN = 2
    DIGITAL_OUT = 3
    COUNTER_IN = 4
    CAPTURE_IN = 5


class Trigger(IntEnum):
    """Valid trigger modes."""
    SW = 0
    DIN1 = 1
    DIN2 = 2
    DIN3 = 3
    DIN4 = 4
    DIN5 = 5
    DIN6 = 6
    ABIG = 10
    ASML = 20


class DAQExperiment(object):
    def analog_setup(self, pinput=1, ninput=0, gain=1, nsamples=20):
        """Configure a channel for a generic stream experiment.
        """
        if not 0 <= nsamples < 255:
            raise ValueError("samples number out of range")

        self.pinput = pinput
        self.ninput = ninput
        self.gain = gain
        self.nsamples = nsamples
        self.signal_data = []
        self.signal_offs = 0

    def trigger_setup(self, mode=Trigger.SW, value=0):
        """Channge the trigger mode of datachannel.

        :param mode: Trigger mode (use :class:`.Trigger`).
        :param value: Value of the trigger mode.
        :raises: ValueError
        """

        if not type(mode) is Trigger:
            raise ValueError("Invalid trigger mode")

        if 1 <= mode <= 6 and value not in [0, 1]:
            raise ValueError("Invalid value of digital trigger")

        self.trg_mode = mode
        self.trg_value = value

    def get_params(self):
        """Return gain, pinput and ninput."""
        return self.gain, self.pinput, self.ninput

    def get_mode(self):
        """Return mode."""
        return self.mode

    def get_preload_data(self):
        """Return preload_data and preload_offset. """
        return self.signal_data, self.signal_offs

    def load_signal(self, data, offset=0):
        if not 1 <= len(data) <= 400:
            raise ValueError('Invalid data length')

        self.signal_data = data
        self.signal_offs = offset

    def add_points(self, points):
        """Write a single point into the ring buffer."""
        self.mutex_ring_buffer.acquire()
        self.ring_buffer.extend(points)
        self.mutex_ring_buffer.release()

    def read(self):
        """Return all available points from the ring buffer."""
        self.mutex_ring_buffer.acquire()
        ret = list(self.ring_buffer)
        self.ring_buffer.clear()
        self.mutex_ring_buffer.release()
        return ret


class DAQStream(DAQExperiment):
    """
    Stream experiment.

    :param mode: Define data source or destination (use :class:`.ExpMode`).
    :param period: Period of the stream experiment (milliseconds) [1:65536]
    :param npoints: Total number of points for the experiment
            [0:65536] (0 indicates continuous acquisition).
    :param continuous: Indicates if experiment is continuous (True) or
        one-shot (False).
    :param buffersize: Buffer size.
    :raises: LengthError (too many experiments at the same time),
        ValueError (values out of range)
    """
    def __init__(self, mode, number, period,
                 npoints=10, continuous=False, buffersize=1000):
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')

        if mode == 1 and number != 4:
            raise ValueError('Analog output must use DataChannel 4')

        if not 1 <= period <= 65535:
            raise ValueError('Invalid period')

        if type(mode) == int and not 0 <= mode <= 5:
            raise ValueError('Invalid mode')

        if not 0 <= npoints < 65536:
            raise ValueError('npoints out of range')

        if not 1 <= buffersize <= 20000:
            raise ValueError('Invalid buffer size')

        self.number = number
        self.period = period
        self.mode = mode
        self.npoints = npoints
        self.continuous = continuous

        self.ring_buffer = deque(maxlen=buffersize)
        self.mutex_ring_buffer = Lock()
        self.analog_setup()
        self.trigger_setup()


class DAQExternal(DAQExperiment):
    """External experiment.

    :param mode: Define data source or destination (use :class:`.ExpMode`).
    :param clock_input: Digital input used as external clock
    :param edge: New data on rising (1) or falling (0) edges [0:1]
    :param npoints: Total number of points for the experiment [0:65536]
    :param continuous: Indicates if the experiment is continuous
        (False: run once, True: continuous).
    :param buffersize: Buffer size
    :raises: LengthError (too many experiments at the same time,
        ValueError (values out of range)
    """
    def __init__(self, mode, clock_input, edge=1,
                 npoints=10, continuous=False, buffersize=1000):

        if not 1 <= clock_input <= 4:
            raise ValueError('Invalid clock_input')

        if edge not in [0, 1]:
            raise ValueError('Invalid edge')

        if type(mode) == int and not 0 <= mode <= 5:
            raise ValueError('Invalid mode')

        if not 0 <= npoints < 65536:
            raise ValueError('npoints out of range')

        if not 1 <= buffersize <= 20000:
            raise ValueError('Invalid buffer size')

        if mode == 1 and clock_input != 4:
            raise ValueError('Analog output must use DataChannel 4')

        self.number = clock_input
        self.edge = edge
        self.mode = mode
        self.npoints = npoints
        self.continuous = continuous

        self.ring_buffer = deque(maxlen=buffersize)
        self.mutex_ring_buffer = Lock()
        self.analog_setup()
        self.trigger_setup()


class DAQBurst(DAQExperiment):
    """Burst experiment.

    :param mode: Define data source or destination (use :class:`.ExpMode`).
    :param period: Period of the stream experiment (microseconds) [1:65536]
    :param npoints: Total number of points for the experiment [0:65536]
    :param continuous: Indicates if the experiment is continuous
        (False: run once, True: continuous).
    :param buffersize: Buffer size
    :raises: LengthError (too many experiments at the same time), ValueError
        (values out of range)
    """
    def __init__(self, mode, period, npoints=10,
                 continuous=False, buffersize=4000):

        if not 100 <= period <= 65535:
            raise ValueError('Invalid period')

        if not 0 <= npoints < 65536:
            raise ValueError('npoints out of range')

        if type(mode) == int and not 0 <= mode <= 1:
            raise ValueError('Invalid mode')

        self.number = 1
        self.period = period
        self.npoints = npoints
        self.continuous = continuous
        self.mode = mode

        self.ring_buffer = deque(maxlen=buffersize)
        self.mutex_ring_buffer = Lock()
        self.analog_setup()
        self.trigger_setup()
