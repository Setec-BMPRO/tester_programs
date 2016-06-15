#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Test Program."""

import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """Trs1 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('BreakAway', self._step_breakaway, None, True),
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

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(
            ((s.oVin, 0.0), (s.o5V, 0.0), (s.oBrake, 0.0), (s.oLight, 0.0),
             (s.oRemote, 0.0), ))

        t.pwr_up.run()

    def _step_breakaway(self):
        """Measure under 'breakaway' condition."""
        self.fifo_push(
            ((s.oVin, 12.0), (s.o5V, 5.0), (s.oBrake, 12.0), (s.oLight, 12.0),
             (s.oRemote, 12.0), (s.oRed, (12.0, 0.0, 12.0)),
             (s.oYesNoGreen, True), (s.tp3, ((0.56,),)), ))

        t.brkaway1.run()
        tester.testsequence.path_push('14V')
        t.brkaway2.run()
        tester.testsequence.path_pop()
        tester.testsequence.path_push('10V')
        t.brkaway3.run()
        tester.testsequence.path_pop()
        tester.testsequence.path_push('11V')
        t.brkaway4.run()
        tester.testsequence.path_pop()
        m.dso_tp3.measure(timeout=5)
