#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Safety Test Program.

Call 'self.abort()' to stop program running at end of current step.
'self._result_map' is a list of 'uut.Result' indexed by position.

"""

import logging
import tester
from . import support
from . import limit

SAF_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Safety(tester.TestSequence):

    """SX-750 Safety Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('Gnd1', self._step_gnd1),
            tester.TestStep('Gnd2', self._step_gnd2),
            tester.TestStep('Gnd3', self._step_gnd3),
            tester.TestStep('HiPot', self._step_hipot),
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
        global m, d, s
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_gnd1(self):
        """Ground Continuity 1."""
        self.fifo_push(((s.gnd1, 40), ))
        m.gnd1.measure()

    def _step_gnd2(self):
        """Ground Continuity 2."""
        self.fifo_push(((s.gnd2, 50), ))
        m.gnd2.measure()

    def _step_gnd3(self):
        """Ground Continuity 3."""
        self.fifo_push(((s.gnd3, 60), ))
        m.gnd3.measure()

    def _step_hipot(self):
        """HiPot Test."""
        self.fifo_push(((s.acw, 3.0), ))
        m.acw.measure()
