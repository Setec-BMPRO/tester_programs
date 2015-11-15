#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE4/5 Final Test Program."""

import logging

import tester
from . import support
from . import limit

LIMIT_DATA4 = limit.DATA4       # BCE4 limits
LIMIT_DATA5 = limit.DATA5       # BCE5 limits

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """BCE4/5 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('FullLoad', self._step_full_load, None, True),
            ('OCP', self._step_ocp, None, True),
            ('LowMains', self._step_low_mains, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # It is BCE4 is FullLoad current > 7.5A
        self._isbce4 = test_limits['FullLoad'].limit > 7.5

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

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
