#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Test Program."""

import logging
import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """Trs1 Initial Test Program."""

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
            ('BreakAway', self._step_breakaway, None, True),
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
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(
            ((s.oVin, 12.0), (s.oPin, 12.0), (s.oBrake, 0.0),
             (s.oLight, 0.0), (s.oRemote, 0.0), ))

        t.pwr_up.run()

    def _step_breakaway(self):
        """Measure under 'breakaway' condition."""
        self.fifo_push(
            ((s.o5V, 5.0), (s.oBrake, 12.0), (s.oLight, 12.0),
             (s.oRemote, 12.0), (s.oGreen, (0.0, 12.0, 0.0)),
             (s.oRed, (12.0, 12.0, 0.0)), (s.oYesNoGreen, True),
             (s.tp11, ((0.8,),)), (s.tp3, ((1.1,),)), (s.tp8, ((2.2,),)),
            ))

        t.brkaway.run()
