#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Final Test Program."""

import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """SX-750 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('InputRes', self._step_inres, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('PowerOn', self._step_poweron, None, True),
            ('Load', self._step_load, None, True),
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
        s = support.Sensors(d)
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

    def _step_inres(self):
        """Verify that the hand loaded input discharge resistors are there."""
        self.fifo_push(((s.oInpRes, 70000), ))

        m.dmm_InpRes.measure(timeout=5)

    def _step_powerup(self):
        """Switch on unit at 240Vac, no load, not enabled."""
        self.fifo_push(
            ((s.oIec, (0.0, 240.0)), (s.o5v, 5.1), (s.o12v, 0.0),
             (s.oYesNoGreen, True)))

        t.pwr_up.run()

    def _step_poweron(self):
        """Enable all outputs and check that the LED goes blue."""
        self.fifo_push(
            ((s.oYesNoBlue, True), (s.o5v, 5.1), (s.oPwrGood, 0.1),
             (s.oAcFail, 5.1), ))

        t.pwr_on.run()

    def _step_load(self):
        """Measure outputs at load."""
        self.fifo_push(
            ((s.o5v, 5.1), (s.o12v, (12.2, 12.1)), (s.o24v, (24.2, 24.1)),
             (s.oPwrGood, 0.1), (s.oAcFail, 5.1), ))

        nl12v, nl24v = MeasureGroup((m.dmm_12von, m.dmm_24von, )).readings
        t.load.run()
        fl12v, fl24v = MeasureGroup((m.dmm_12vfl, m.dmm_24vfl, )).readings
        if self.running:
            reg12v = 100 * (nl12v - fl12v) / nl12v
            reg24v = 100 * (nl24v - fl24v) / nl24v
            s.oMir12v.store(reg12v)
            s.oMir24v.store(reg24v)
            MeasureGroup((m.reg12v, m.reg24v, ))
