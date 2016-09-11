#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Initial Test Program."""

import logging

import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """2040 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('SecCheck', self._step_sec_check),
            tester.TestStep('DCPowerOn', self._step_dcpower_on),
            tester.TestStep('ACPowerOn', self._step_acpower_on),
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

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.oLock, 10.0), ))

        m.dmm_Lock.measure(timeout=5)

    def _step_sec_check(self):
        """Apply External DC voltage to output and measure voltages."""
        self.fifo_push(((s.oVout, 20.0), (s.oSD, 20.0), (s.oGreen, 17.0), ))

        t.sec_chk.run()

    def _step_dcpower_on(self):
        """Test with DC power in.

        Power with DC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        self.fifo_push(
            ((s.oDCin, (10.0, 40.0, 25.0)), (s.oGreen, 17.0),
             (s.oRedDC, (12.0, 2.5)), (s.oVccDC, (12.0,) * 3),
             (s.oVout, (20.0, ) * 15 + (18.0, ), ), (s.oSD, 4.0),))

        t.dcpwr_on.run()

    def _step_acpower_on(self):
        """Test with AC power in.

        Power with AC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        self.fifo_push(
            ((s.oACin, (90.0, 265.0, 240.0)), (s.oGreen, 17.0),
             (s.oRedAC, 12.0), (s.oVbus, (130.0, 340)),
             (s.oVccAC, (13.0,) * 3), (s.oVout, (20.0, ) * 15 + (18.0, ), ), ))

        t.acpwr_on.run()
