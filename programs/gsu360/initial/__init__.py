#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSU360-1TA Initial Test Program."""

import logging
import time

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """GSU360-1TA Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FixtureLock', self._step_fixture_lock, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('FullLoad', self._step_full_load, None, True),
            ('OCP', self._step_ocp, None, True),
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
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

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
        d.acsource.output(voltage=0.0, output=False)
        d.dcl_24V.output(5.0)
        time.sleep(1)
        d.discharge.pulse()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.Lock, 10.0), ))
        m.dmm_Lock.measure(timeout=5)

    def _step_power_up(self):
        """Power up unit at 92Vac and measure primary voltages."""
        self.fifo_push(
            ((s.ACin, 92.0), (s.PFC, 400.0), (s.PriCtl, 13.0),
             (s.PriVref, 7.4), (s.o24V, 24.0), (s.Fan12V, 12.0),
             (s.SecCtl, 24.0), (s.SecVref, 2.5),))
        t.pwr_up.run()

    def _step_full_load(self):
        """Power up unit at 240Vac, load and measure secondary voltages."""
        self.fifo_push(((s.o24V, 24.0), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.o24V, (24.0, ) * 15 + (23.0, ), ), ))
        m.ramp_OCP.measure()