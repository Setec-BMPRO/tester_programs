#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Test Program."""

import logging
import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """Trs1 Initial Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('BreakAway', self._step_breakaway),
            tester.TestStep('BattLow', self._step_batt_low),
            )
        # Set the Test Sequence in my base instance
        super().__init__(sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self, parameter):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d)
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
        """Apply 12Vdc input and measure voltages."""
        self.fifo_push(
            ((s.oVin, 0.0), (s.o5V, 0.0), (s.oBrake, 0.0), (s.oLight, 0.0),
             (s.oRemote, 0.0), ))

        t.pwr_up.run()

    def _step_breakaway(self):
        """Measure voltages under 'breakaway' condition."""
        self.fifo_push(
            ((s.oVin, 12.0), (s.o5V, 5.0), (s.oBrake, 12.0), (s.oLight, 12.0),
             (s.oRemote, 12.0), (s.oRed, 10.0), (s.oYesNoGreen, True),
             (s.tp3, ((0.56,),)), ))

        t.brkaway.run()

    def _step_batt_low(self):
        """Check operation of Red Led under low battery condition."""
        self.fifo_push(
            ((s.oRed, (0.0, 10.0)), ))

        t.lowbatt.run()
