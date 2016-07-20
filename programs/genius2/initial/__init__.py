#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initial Test Program for GENIUS-II and GENIUS-II-H."""

import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

INI_LIMIT = limit.DATA         # GENIUS-II limits
INI_LIMIT_H = limit.DATA_H      # GENIUS-II-H limits


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """GENIUS-II Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_powerup, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # It is a GENIUS-II-H if BattLoad current > 20A
        self._fullload = test_limits['MaxBattLoad'].limit
        self._isH = (self._fullload > 20)

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

    def _step_powerup(self):
        """Switch on unit at 240Vac, no load."""
        self.fifo_push(((s.oVout, 13.6), ))

        t.pwrup.run()
