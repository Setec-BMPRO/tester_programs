#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Initial Test Program."""

import logging
import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """C15A-15 Initial Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('Power90', self._step_power_90),
            tester.TestStep('Power240', self._step_power_240),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('PowerOff', self._step_power_off),
            )
        # Set the Test Sequence in my base instance
        super().__init__(sequence, fifo)
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
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_power_90(self):
        """Power up at 90Vac."""
        self.fifo_push(
            ((s.vin, 90.0), (s.vbus, 130), (s.vcc, 9), (s.vout, 15.5),
             (s.green, 11), (s.yellow, 0.2),))
        t.pwr_90.run()

    def _step_power_240(self):
        """Power up at 240Vac."""
        self.fifo_push(
            ((s.vin, 240.0), (s.vbus, 340), (s.vcc, 12), (s.vout, 15.5),
             (s.green, 11), (s.yellow, 0.2),))
        t.pwr_240.run()

    def _step_ocp(self):
        """Measure OCP."""
        self.fifo_push(
            ((s.vout, (15.5, ) * 15 + (13.5, ), ),
             (s.yellow, 8), (s.green, 9), (s.vout, (10, 15.5)), ))
        t.ocp.run()

    def _step_power_off(self):
        """Input AC off and discharge."""
        t.pwr_off.run()
