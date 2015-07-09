#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Test Program."""

import os
import logging

import tester
import share.programmer
import share.arm
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'\\.\COM2',
             }[os.name]


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """Trek2 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self._armdev = share.arm.Console(port=_ARM_PORT)
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._armdev.close()
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(((s.oVin, 12.0), ))

        t.pwr_up.run()

