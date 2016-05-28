#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMU750-70 Final Test Program."""

import logging

import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """SMU750-70 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('FullLoad', self._step_full_load, None, True),
            ('OCP', self._step_ocp, None, True),
            ('Shutdown', self._step_shutdown, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
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
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_power_up(self):
        """Switch on at 240Vac, measure output at min load."""
        self.fifo_push(((s.o70V, 70.0), (s.oYesNoFan, True), ))
        t.pwr_up.run()

    def _step_full_load(self):
        """Measure output at full load (11.3A +/- 150mA)."""
        self.fifo_push(((s.o70V, 70.0), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.o70V, (70.0, ) * 15 + (69.2, ), ), ))
        m.ramp_OCP.measure()

    def _step_shutdown(self):
        """Overload and shutdown unit, re-start."""
        self.fifo_push(((s.o70V, (10.0, 70.0)), ))
        t.shdn.run()
