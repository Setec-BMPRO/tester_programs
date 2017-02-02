#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ETrac-II Initial Test Program."""

import logging
import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """ETrac-II Initial Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not fifo),
            tester.TestStep('Load', self._step_load),
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
        """Apply input DC and measure voltages."""
        self.fifo_push(((s.oVin, 13.0), (s.oVin2, 12.0),
                         (s.o5V, 5.0), ))

        t.pwr_up.run()

    def _step_program(self):
        """Program the PIC micro."""
        d.program_pic.program()

    def _step_load(self):
        """Load and measure voltages."""
        self.fifo_push(((s.o5Vusb, 5.1), (s.oVbat, (8.45, 8.4)), ))

        t.load.run()
