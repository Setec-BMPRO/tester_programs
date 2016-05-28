#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C45A-15 Final Test Program."""

import logging

import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.testsequence.TestSequence):

    """C45A-15 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('ConnectCMR', self._step_connect_cmr, None, True),
            ('Load', self._step_load, None, True),
            ('Restart', self._step_restart, None, True),
            ('Poweroff', self._step_power_off, None, True),
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
        global m, d, s, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_power_up(self):
        """Switch on unit at 240Vac, measure output, check Green led."""
        self.fifo_push(((s.oVout, 9.0), (s.oYesNoGreen, True), ))
        t.pwr_up.run()

    def _step_connect_cmr(self):
        """
        Connect the CMR-SBP Bus, measure output, check Yellow and Red leds.
        """
        self.fifo_push(
            ((s.oYesNoYellow, True), (s.oVout, 16.0), (s.oYesNoRed, True), ))
        t.connect_cmr.run()

    def _step_load(self):
        """Measure output at startup load, full load, and shutdown load."""
        self.fifo_push(((s.oVout, 16.0), (s.oVout, 16.0), (s.oVout, 0.0), ))
        t.load.run()

    def _step_restart(self):
        """Restart the unit, measure output."""
        self.fifo_push(((s.oVout, 9.0), ))
        t.restart.run()

    def _step_power_off(self):
        """Switch off unit, measure output."""
        self.fifo_push(((s.oVout, 0.0), (s.oNotifyOff, True), ))
        t.pwr_off.run()
