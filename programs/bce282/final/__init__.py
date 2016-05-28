#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Final Program."""

# FIXME: This program is not finished yet!

import logging

import tester
from . import support
from . import limit

FIN_LIMIT_12 = limit.DATA12       # BCE282-12 limits
FIN_LIMIT_24 = limit.DATA24       # BCE282-24 limits

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """BCE282-12/24 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
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
        # It is BCE282-12 if FullLoad current > 15.0A
        self._isbce12 = test_limits['FullLoad'].limit > 15.0

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
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

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_power_up(self):
        """Power up unit."""
        self.fifo_push(((s.oAlarm, (1, 10000)), ))
        if self._isbce12:
            self.fifo_push(((s.oVout, (13.6, 13.55)), (s.oVbat, 13.3), ))
        else:
            self.fifo_push(((s.oVout, (27.6, 27.6)), (s.oVbat, 27.5), ))
        t.power_up.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(((s.oYesNoGreen, True), ))
        if self._isbce12:
            self.fifo_push(((s.oVout, 13.4), (s.oVbat, 13.3), ))
        else:
            self.fifo_push(((s.oVout, 27.2), (s.oVbat, 27.1), ))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP point."""
        if self._isbce12:
            self.fifo_push(((s.oVout, (13.4, ) * 15 + (13.0, ), ),
                            (s.oVbat, (13.4, ) * 15 + (13.0, ), ), ))
        else:
            self.fifo_push(((s.oVout, (27.3, ) * 8 + (26.0, ), ),
                            (s.oVbat, (27.3, ) * 8 + (26.0, ), ), ))
        m.ramp_OCPLoad.measure()
        d.dcl_Vout.output(0.0)
        m.ramp_OCPBatt.measure()
        d.dcl_Vbat.output(0.0)
