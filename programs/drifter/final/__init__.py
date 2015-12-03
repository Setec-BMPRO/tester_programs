#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Final Test Program."""

import logging
import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA
LIMIT_DATA_BM = limit.DATA_BM

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """Drifter Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('DisplayCheck', self._step_displ_check, None, True),
            ('SwitchCheck', self._step_sw_check, None, True),
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
        s = support.Sensors(d)
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

        MeasureGroup(
            (m.ui_NotifySwOff, m.dmm_PumpOff, m.dmm_BattDisconn,
             m.ui_NotifySwOn, m.dmm_PumpOn, m.dmm_BattConnect, m.dmm_USB5V),
            timeout=5)
