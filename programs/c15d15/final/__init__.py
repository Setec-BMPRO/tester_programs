#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Final(tester.TestSequence):

    """C15D-15 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('OCP', self._step_ocp, None, True),
            ('FullLoad', self._step_full_load, None, True),
            ('Recover', self._step_recover, None, True),
            ('PowerOff', self._step_power_off, None, True),
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
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_power_up(self):
        """Power up with 12Vdc, measure output, check Green and Yellow leds."""
        self.fifo_push(
            ((s.oVout, 15.0), (s.oYesNoGreen, True),
             (s.oYesNoYellowOff, True), (s.oNotifyYellow, True),))

        t.pwr_up.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(
            ((s.oVout, (15.0, ) * 5 + (13.5, ), ),
             (s.oYesNoYellowOn, True), (s.oVout, 15.0), ))

        t.ocp.run()

    def _step_full_load(self):
        """Measure output at full load."""
        self.fifo_push(((s.oVout, 4.0), ))

        t.full_load.run()

    def _step_recover(self):
        """Recover from full load."""
        self.fifo_push(((s.oVout, 15.0), ))

        t.recover.run()

    def _step_power_off(self):
        """Input DC off and discharge."""
        t.pwr_off.run()
