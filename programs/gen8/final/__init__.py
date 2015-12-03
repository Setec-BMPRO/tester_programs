#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 Final Test Program."""

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

    """GEN8 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('PowerOn', self._step_power_on, None, True),
            ('FullLoad', self._step_full_load, None, True),
            ('115V', self._step_115v, None, True),
            ('Poweroff', self._step_power_off, None, True),
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

    def _step_power_up(self):
        """Switch on at 240Vac, not enabled, measure output at min load."""
        self.fifo_push(
            ((s.o5V, 5.1), (s.o24V, 0.0), (s.o12V, 0.0), (s.o12V2, 0.0), ))
        t.pwr_up.run()

    def _step_power_on(self):
        """Enable outputs, measure voltages at min load."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o12V, 12.0), (s.o12V2, 0.0),
             (s.oPwrFail, 24.1), (s.o12V2, 12.0), (s.oYesNoMains, True),
             (s.oIec, 240.0), ))
        t.pwr_on.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(
            ((s.o5V, 5.1), (s.o24V, 24.1), (s.o12V, 12.1), (s.o12V2, 12.2)))
        t.full_load.run()

    def _step_115v(self):
        """Measure outputs at 115Vac in, full-load."""
        self.fifo_push(
            ((s.o5V, 5.1), (s.o24V, 24.1), (s.o12V, 12.1), (s.o12V2, 12.2)))
        t.full_load_115.run()

    def _step_power_off(self):
        """Switch off unit, measure gpo and 24V voltages."""
        self.fifo_push(
            ((s.oNotifyPwrOff, True), (s.oIec, 0.0), (s.o24V, 0.0)))
        t.pwr_off.run()
