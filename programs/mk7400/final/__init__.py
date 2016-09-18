#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MK7-400-1 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """MK7-400-1 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('115V', self._step_115v),
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

    def _step_power_up(self):
        """
        Switch on unit at 240Vac, not enabled.

        Measure output voltages at min load.

        """
        self.fifo_push(((s.o5V, 5.1), (s.o12V, 0.0),
                         (s.o24V, 0.0), (s.o24V2, 0.0), ))
        t.pwr_up.run()

    def _step_power_on(self):
        """Enable outputs, measure voltages at min load."""
        self.fifo_push(
            ((s.o12V, 12.0), (s.o24V, 24.0), (s.o24V2, 0.0),
            (s.oPwrFail, 24.1), (s.o24V2, 24.0), (s.oYesNoMains, True),
            (s.oAux, 240.0), (s.oAuxSw, 240.0), ))
        t.pwr_on.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(
            ((s.o5V, 5.1), (s.o12V, 12.1), (s.o24V, 24.1), (s.o24V2, 24.2), ))
        t.full_load.run()

    def _step_115v(self):
        """Measure outputs at 115Vac in, full-load."""
        self.fifo_push(
            ((s.o5V, 5.1), (s.o12V, 12.1), (s.o24V, 24.1), (s.o24V2, 24.2), ))
        t.full_load_115.run()

    def _step_power_off(self):
        """Switch off unit, measure Aux and 24V voltages."""
        self.fifo_push(
            ((s.oNotifyPwrOff, True), (s.oAux, 0.0), (s.oAuxSw, 0.0),
             (s.o24V, 0.0), ))
        t.pwr_off.run()
