#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """2040 Final Test Program."""

    def __init__(self, per_panel, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('DCPowerOn', self._step_dcpower_on),
            tester.TestStep('DCLoad', self._step_dcload),
            tester.TestStep('ACPowerOn', self._step_acpower_on),
            tester.TestStep('ACLoad', self._step_acload),
            tester.TestStep('Recover', self._step_recover),
            )
        # Set the Test Sequence in my base instance
        super().__init__(per_panel, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
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

    def _step_dcpower_on(self):
        """Startup with DC Input, measure output at no load."""
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
