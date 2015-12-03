#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Final Test Program."""

import logging
import tester
from . import support
from . import limit

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """2040 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('DCPowerOn', self._step_dcpower_on, None, True),
            ('DCLoad', self._step_dcload, None, True),
            ('ACPowerOn', self._step_acpower_on, None, True),
            ('ACLoad', self._step_acload, None, True),
            ('Recover', self._step_recover, None, True),
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
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_dcpower_on(self):
        """Startup with DC Input, measure output at no load.

        Check AC Power led.

        """
        self.fifo_push(
            ((s.o20V, 20.0), (s.oYesNoGreen, True), (s.o20V, 20.0), ))
        t.dcpwr_on.run()

    def _step_dcload(self):
        """Measure output at full load with DC Input.

        Check the "OFF" function of the DC Fault led.

        """
        self.fifo_push(((s.o20V, 20.0), (s.oYesNoDCOff, True), ))
        t.full_load.run()

    def _step_acpower_on(self):
        """Startup with AC Input, measure output at no load."""
        self.fifo_push(((s.o20V, 20.0), ))
        t.acpwr_on.run()

    def _step_acload(self):
        """Measure output at peak load with AC Input.

        Check the AC Fault led.

        """
        self.fifo_push(
            ((s.o20V, 20.0), (s.oYesNoACOff, True),
             (s.o20V, 0.0), (s.oYesNoACOn, True), ))
        t.peak_load.run()

    def _step_recover(self):
        """Check recovery after shutdown."""
        self.fifo_push(((s.o20V, 0.0), (s.o20V, 20.0), ))
        t.recover.run()
