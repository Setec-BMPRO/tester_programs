#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSU360-1TA Final Test Program."""

import logging

import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """GSU360-1TA Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('FullLoad', self._step_full_load, None, True),
            ('OCP', self._step_ocp, None, True),
            ('Shutdown', self._step_shutdown, None, True),
            ('Restart', self._step_restart, None, True),
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

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_power_up(self):
        """Power up unit at 240Vac."""
        self.fifo_push(((s.o24V, 24.00), (s.oYesNoGreen, True)))
        t.pwr_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(((s.o24V, 24.10), (s.o24V, 24.00)))
        d.dcl_24V.binary(0.0, 15.0, 4.0)
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.o24V, (24.1, ) * 15 + (22.0, ), ), ))
        # Load is already at 15.0A
        m.ramp_24Vocp.measure()

    def _step_shutdown(self):
        """Overload unit, measure."""
        self.fifo_push(((s.o24V, 4.0), ))
        # Shutdown: Overload unit, measure
        # Load is already at OCP point
        d.dcl_24V.output(21.0)
        m.dmm_24Voff.measure(timeout=5)

    def _step_restart(self):
        """Re-Start unit after Shutdown."""
        self.fifo_push(((s.o24V, 24.0), ))
        d.dcl_24V.output(0.0)
        m.dmm_24V.measure(timeout=5)
