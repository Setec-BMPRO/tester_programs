#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Main Test Program."""

import logging
import tester
from . import support
from . import limit

INI_MAIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class InitialMain(tester.testsequence.TestSequence):

    """IDS-500 Initial Main Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('PowerUp', self._step_power_up),
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
        global d, s, m, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.Lock, 10.0), ))

        m.dmm_Lock.measure(timeout=5)

    def _step_power_up(self):
        """Set min load, apply input AC and measure voltages."""
        self.fifo_push(
            ((s.oVbus, 340.0), (s.oTec, 0.0), (s.oTecVmon, 0.0),
             (s.oLdd, 0.0), (s.oIsVmon, 0.0), (s.o15V, 0.0), (s.om15V, 0.0),
             (s.o15Vp, 0.0), (s.o15VpSw, 0.0), (s.o5V, 0.0), ))

        t.pwr_up.run()
