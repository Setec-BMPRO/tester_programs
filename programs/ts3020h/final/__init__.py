#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TS3020H Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """TS3020H Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('FuseCheck', self._step_fuse_check),
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Poweroff', self._step_power_off),
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
