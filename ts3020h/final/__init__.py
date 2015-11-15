#!/usr/bin/env python3
"""TS3020H Final Test Program."""

import logging

import tester
from . import support
from . import limit

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """TS3020H Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FuseCheck', self._step_fuse_check, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('FullLoad', self._step_full_load, None, True),
            ('OCP', self._step_ocp, None, True),
            ('Poweroff', self._step_power_off, None, True),
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
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_fuse_check(self):
        """
        Powerup with output fuse removed, measure output off.

        Check Mains light and Red led.

        """
        self.fifo_push(
            ((s.oNotifyStart, True), (s.o12V, 0.0), (s.oYesNoRed, True),
             (s.oNotifyFuse, True), ))
        t.fuse_check.run()

    def _step_power_up(self):
        """Switch on unit at 240Vac, measure output voltages at no load."""
        self.fifo_push(((s.o12V, 13.8), (s.oYesNoGreen, True), ))
        t.pwr_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(((s.o12V, 13.6), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.o12V, (13.4, ) * 15 + (13.0, ), ), ))
        m.ramp_OCP.measure()

    def _step_power_off(self):
        """Switch off unit, measure output voltage."""
        self.fifo_push(
            ((s.oNotifyMains, True), (s.o12V, 0.0), (s.oYesNoOff, True), ))
        t.pwr_off.run()
