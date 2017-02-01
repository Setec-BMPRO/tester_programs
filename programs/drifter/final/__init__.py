#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA
FIN_LIMIT_BM = limit.DATA_BM

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """Drifter Final Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('DisplayCheck', self._step_displ_check),
            tester.TestStep('SwitchCheck', self._step_sw_check),
            )
        # Set the Test Sequence in my base instance
        super().__init__(sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global m, d, s, t
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

    def _step_displ_check(self):
        """Apply DC Input voltage and check the display."""
        self.fifo_push(
            ((s.oYesNoSeg, True), (s.oYesNoBklight, True),
             (s.oYesNoDisplay, True), ))

        t.displ_check.run()

    def _step_sw_check(self):
        """Check the operation of the rocker switches, check USB 5V."""
        self.fifo_push(
            ((s.oNotifySwOff, True), (s.oWaterPump, 0.1), (s.oBattSw, 0.1),
             (s.oNotifySwOn, True), (s.oWaterPump, 11.0), (s.oBattSw, 11.0),
             (s.oUSB5V, 5.0), ))

        tester.MeasureGroup(
            (m.ui_NotifySwOff, m.dmm_PumpOff, m.dmm_BattDisconn,
             m.ui_NotifySwOn, m.dmm_PumpOn, m.dmm_BattConnect, m.dmm_USB5V),
            timeout=5)
