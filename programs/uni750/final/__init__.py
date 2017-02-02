#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UNI-750 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """UNI-750 Final Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('FullLoad', self._step_full_load),
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
        """Connect unit to 240Vac, Remote AC Switch off."""
        self.fifo_push(((s.oAcUnsw, 240.0), (s.oAcSw, 0.0), ))
        t.pwr_up.run()

    def _step_power_on(self):
        """Remote AC Switch on, measure outputs at min load."""
        self.fifo_push(
            ((s.oAcSw, 240.0), (s.oYesNoFan, True), (s.o24V, 24.5),
             (s.o15V, 15.0), (s.o12V, 12.0), (s.o5V, 5.1),
             (s.o3V3, 3.3), (s.o5Vi, 5.2), (s.oPGood, 5.2), ))
        t.pwr_on.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o15V, 15.0), (s.o12V, 12.0),
             (s.o5V, 5.1), (s.o3V3, 3.3), (s.o5Vi, 5.15),
             (s.oPGood, 5.2), ))
        t.full_load.run()
