#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Final(tester.TestSequence):

    """BC15 Final Test Program."""

    def __init__(self, per_panel, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerOn', self._step_poweron),
            tester.TestStep('Load', self._step_loaded),
            )
        # Set the Test Sequence in my base instance
        super().__init__(per_panel, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_poweron(self):
        """Power up the Unit and measure output with min load."""
        self.fifo_push(((s.ps_mode, True), (s.vout, 13.80), ))

        d.dcl.output(1.0, output=True)
        d.acsource.output(240.0, output=True)
        tester.MeasureGroup((m.ps_mode, m.vout_nl, ), timeout=5)

    def _step_loaded(self):
        """Load the Unit."""
        self.fifo_push(
            ((s.vout, (14.23, ) + (14.2, ) * 8 + (11.0, )),
             (s.ch_mode, True), ))

        d.dcl.output(10.0)
        tester.MeasureGroup((m.vout, m.ocp, m.ch_mode, ), timeout=5)
