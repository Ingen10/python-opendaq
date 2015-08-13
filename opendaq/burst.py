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

from opendaq.experiment import DAQExperiment


class DAQBurst(DAQExperiment):
    def __init__(self, period, mode, npoints, continuous, buffersize):
        """
        Class constructor
        """
        if not 1 <= period <= 65535:
            raise ValueError('Invalid period')

        if not 0 <= npoints < 65536:
            raise ValueError('npoints out of range')

        if type(mode) == int and not 0 <= mode <= 5:
            raise ValueError('Invalid mode')

        self.number = 1
        self.period = period
        self.npoints = npoints
        self.continuous = continuous
        self.mode = mode
        self.ring_buffer_size = buffersize + 1
        self.ring_buffer = [None] * self.ring_buffer_size
        self.ring_buffer_start = 0
        self.ring_buffer_end = 0
        self.mutex_ring_buffer = Lock()        
        self.analog_setup()

    def analog_setup(self, pinput=1, ninput=0, gain=1, nsamples=20):
        """
        Configure a channel for a generic stream experiment.
        """
        if not 0 <= pinput <= 8:
            raise ValueError('pinput out of range')

        if not 0 <= nsamples < 255:
            raise ValueError("samples number out of range")

        
        self.pinput = pinput
        self.ninput = ninput
        self.gain = gain
        self.nsamples = nsamples

    def get_parameters(self):
        """
        Return gain, pintput and ninput
        """
        return self.gain, self.pinput, self.ninput, self.number

    def get_mode(self):
        """
        Return mode
        """
        return self.mode

    def get_preload_data(self):
        """
        Return preload_data and preload_offset
        """
        return self.preload_data, self.preload_offset
    
    def load_signal(self, data, offset=0, clear=False):
        """
        Load an array of values in volts to preload DAC output
        """
        if not 1 <= len(data) <= 400:
            raise ValueError('Invalid data length')

        if clear:
            self.preload_data = []
            self.preload_offset = []

        self.preload_data.append(data)
        self.preload_offset.append(offset)

    def add_point(self, point):
        """
        Write a single point into the ring buffer
        """
        self.mutex_ring_buffer.acquire()

        self.ring_buffer[self.ring_buffer_end] = point
        self.ring_buffer_end += 1
        if self.ring_buffer_end >= self.ring_buffer_size:
            self.ring_buffer_end = 0

        if self.ring_buffer_end == self.ring_buffer_start:
            self.ring_buffer_end -= 1
        if self.ring_buffer_end < 0:
            self.ring_buffer_end = self.ring_buffer_size-1

        self.mutex_ring_buffer.release()

    def read(self):
        """
        Return all available points from the ring buffer
        """
        buffer = []
        self.mutex_ring_buffer.acquire()

        if self.ring_buffer_start < self.ring_buffer_end:
            for i in range(self.ring_buffer_start, self.ring_buffer_end):
                buffer.append(self.ring_buffer[i])

        if self.ring_buffer_start > self.ring_buffer_end:
            for i in range(self.ring_buffer_start, self.ring_buffer_size):
                buffer.append(self.ring_buffer[i])

            for i in range(0, self.ring_buffer_end):
                buffer.append(self.ring_buffer[i])

        self.ring_buffer_start = self.ring_buffer_end = 0
        self.mutex_ring_buffer.release()
        return buffer

