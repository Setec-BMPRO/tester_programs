#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE4/5 Final Test Program."""

import logging
import tester
from . import support
from . import limit

LIMIT_DATA4 = limit.DATA4       # BCE4 limits
LIMIT_DATA5 = limit.DATA5       # BCE5 limits

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """BCE4/5 Final Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('LowMains', self._step_low_mains),
            )
        # Set the Test Sequence in my base instance
        super().__init__(sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # It is BCE4 is FullLoad current > 7.5A
        self._isbce4 = test_limits['FullLoad'].limit > 7.5

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global m, d, s, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m, self._limits)

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
        """Power up unit."""
        if self._isbce4:
            self.fifo_push(
                ((s.oVout, (13.6, 13.55)), (s.oVbat, 13.3),
                 (s.oAlarm, (0.1, 10.0)), ))
        else:
            self.fifo_push(
                ((s.oVout, (27.3, 27.2)), (s.oVbat, 27.2),
                 (s.oAlarm, (0.1, 10.0)), ))
        t.power_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        if self._isbce4:
            self.fifo_push(((s.oVout, 13.4), (s.oVbat, 13.3), ))
        else:
            self.fifo_push(((s.oVout, 27.2), (s.oVbat, 27.1), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        if self._isbce4:
            self.fifo_push(((s.oVout, (13.4, ) * 15 + (13.0, ), ), ))
        else:
            self.fifo_push(((s.oVout, (27.3, ) * 8 + (26.0, ), ), ))
        # Load is already at FullLoad
        m.ramp_OCP.measure()

    def _step_low_mains(self):
        """Low input voltage."""
        if self._isbce4:
            self.fifo_push(((s.oVout, (13.4, ) * 17 + (13.0, ), ), ))
        else:
            self.fifo_push(((s.oVout, (27.3, ) * 17 + (26.0, ), ), ))
        t.low_mains.run()
