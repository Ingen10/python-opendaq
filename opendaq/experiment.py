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

import abc

class DAQExperiment:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, number, period, edge, mode,
                 npoints, continuous, buffersize):
        """
        Class constructor

        Args:
            number: Assign a DataChannel number for this experiment [0:3]
            period: Period of the experiment
            (milliseconds if Stream, microseconds if Burst) [1:65536]
            edge: New data on rising (1) or falling (0) edges [0:1]
            mode: Define data source or destination [0:5]:
                0) ANALOG_INPUT
                1) ANALOG_OUTPUT
                2) DIGITAL_INPUT
                3) DIGITAL_OUTPUT
                4) COUNTER_INPUT
                5) CAPTURE INPUT
            npoints: Total number of points for the experiment
            [0:65536] (0 indicates continuous acquisition)
            continuous: Indicates if experiment is continuous
                False run once
                True continuous
            buffersize: Buffer size

        Raises:
            ValueError: Invalid values
        """      

    @abc.abstractmethod
    def analog_setup(self, pinput, ninput, gain, nsamples):
        """
        Configure a channel for a generic stream experiment.

        Args:
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

    @abc.abstractmethod
    def get_parameters(self):
        """
        Return gain, pinput and ninput
        """

    @abc.abstractmethod
    def get_mode(self):
        """
        Return mode
        """
    
    @abc.abstractmethod
    def get_preload_data(self):
        """
        Return preload_data and preload_offset
        """

    @abc.abstractmethod
    def load_signal(self, data, offset, clear):
        """
        Load an array of values in volts to preload DAC output

        Args:
            data: Total number of data points [1:400]
            offset: Offset for each value
            clear: If true: erase the buffer
        Raises:
            LengthError: Invalid data length
        """

    @abc.abstractmethod
    def add_point(self, point):
        """
        Write a single point into the ring buffer

        Args:
            - point: Point to write into the buffer
        """

    @abc.abstractmethod
    def read(self):
        """
        Return all available points from the ring buffer
        """    

