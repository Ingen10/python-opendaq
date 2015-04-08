#!/usr/bin/env python

# Copyright 2015
# Armando Vincelle <armando@ingen10.com>
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

from threading import Lock
from opendaq.experiment import DAQExperiment

class DAQStream(DAQExperiment):
    def __init__(self, number, size):
        """
        Class constructor

        Args:
            number: Assign a DataChannel number for this experiment [0:3]
            size: Buffer size
            daq: DAQ object
        Raises:
            ValueError: Invalid values
        """
        if not 1 <= number <= 4:
            raise ValueError('Invalid number')
            
        if not 1 <= size <= 20000:
            raise ValueError('Invalid buffer size')

        self.number = number
        self.circular_buffer_size = size + 1
        self.circular_buffer = [None] * self.circular_buffer_size
        self.circular_buffer_start = 0
        self.circular_buffer_end = 0
        self.mutex_circular_buffer = Lock()

    def setup(self, period, npoints, mode, pinput=1, ninput=0, gain=1, nsamples=1, continuous=True):
        """
        Configure a channel for a generic stream experiment.

        Args:
            period: Period of the stream experiment
            (milliseconds) [1:65536]
            npoints: Total number of points for the experiment
            [0:65536] (0 indicates continuous acquisition)
            continuous: Indicates if experiment is continuous
                False continuous
                True run once
            mode: Define data source or destination [0:5]:
                0) ANALOG_INPUT
                1) ANALOG_OUTPUT
                2) DIGITAL_INPUT
                3) DIGITAL_OUTPUT
                4) COUNTER_INPUT
                5) CAPTURE INPUT

            pinput: Select Positive/SE analog input [1:8]
            ninput: Select Negative analog input:
                openDAQ[M]= [0, 5, 6, 7, 8, 25]
                openDAQ[S]= [0,1:8] (must be 0 or pinput-1)

            gain: Select PGA multiplier.
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

            nsamples: Number of samples to calculate the mean for each point\
                 [0:255].
        Raises:
            ValueError: Values out of range
        """
        if not 1 <= period <= 65535:
            raise ValueError('Invalid period')

        if not 0 <= npoints < 65536:
            raise ValueError('npoints out of range')
            
        if type(mode) == int and not 0 <= mode <= 5:
            raise ValueError('Invalid mode')

        if not 0 <= pinput <= 8:
            raise ValueError('pinput out of range')

        if not 0 <= nsamples < 255:
            raise ValueError("samples number out of range")

        self.period = period
        self.npoints = npoints
        self.continuous = continuous
        self.mode = mode
        self.pinput = pinput
        self.ninput = ninput
        self.gain = gain
        self.nsamples = nsamples

    def add_point(self, point):
        """
        Write a single point into the circular buffer

        Args:
            - point: Point to write into the buffer
        """
        self.mutex_circular_buffer.acquire()
        
        self.circular_buffer[self.circular_buffer_end] = point
        self.circular_buffer_end += 1
        if self.circular_buffer_end >= self.circular_buffer_size:
            self.circular_buffer_end = 0
            
        if self.circular_buffer_end == self.circular_buffer_start:
            self.circular_buffer_end -= 1
        if self.circular_buffer_end < 0:
            self.circular_buffer_end = self.circular_buffer_size-1
            
        self.mutex_circular_buffer.release()
        
    def read(self):
        """
        Return all available points from the circular buffer
        """
        buffer = []
        self.mutex_circular_buffer.acquire()
            
        if self.circular_buffer_start < self.circular_buffer_end:
            for i in range (self.circular_buffer_start, self.circular_buffer_end):
                buffer.append(self.circular_buffer[i])
                
        if self.circular_buffer_start > self.circular_buffer_end:            
            for i in range (self.circular_buffer_start, self.circular_buffer_size):
                buffer.append(self.circular_buffer[i])
                
            for i in range (0, self.circular_buffer_end):
                buffer.append(self.circular_buffer[i])

        self.circular_buffer_start = self.circular_buffer_end = 0
        self.mutex_circular_buffer.release()
        return buffer
        