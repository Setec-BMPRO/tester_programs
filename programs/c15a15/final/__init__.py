#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """C15A-15 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('PowerOff', self._step_power_off),
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
        """
        Power up with 240Vac, measure output, check Green and Yellow leds.
        """
        self.fifo_push(
            ((s.oVout, 15.5), (s.oYesNoGreen, True),
             (s.oYesNoYellowOff, True), (s.oNotifyYellow, True),))
        t.pwr_up.run()

    def _step_ocp(self):
        """Measure OCP."""
        self.fifo_push(
            ((s.oVout, (15.5, ) * 5 + (13.5, ), ),
             (s.oYesNoYellowOn, True), (s.oVout, 15.5), ))
        t.ocp.run()

    def _step_full_load(self):
        """Measure output at full load and after recovering."""
        self.fifo_push(((s.oVout, 4.0), (s.oVout, 15.5), ))
        t.full_load.run()

    def _step_power_off(self):
        """Input AC off and discharge."""
        t.pwr_off.run()
