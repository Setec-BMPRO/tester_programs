#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ATXG-450-2V Final Test Program."""

import logging

import tester
from . import support
from . import limit

FIN2V_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final2V(tester.TestSequence):

    """ATXG-450-2V Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('SwitchOn', self._step_switch_on),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('PowerFail', self._step_power_fail),
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

    def _step_power_up(self):
        """Switch on unit at 240Vac, not enabled, measure output voltages."""
        self.fifo_push(
            ((s.o5Vsb, 5.10), (s.oYesNoGreen, True), (s.o24V, 0.0),
             (s.o12V, 0.0), (s.o5V, 0.0), (s.o3V3, 0.0), (s.on12V, 0.0),
             (s.oPwrGood, 0.1), (s.oPwrFail, 5.0)))
        t.pwr_up.run()

    def _step_switch_on(self):
        """Enable outputs, measure."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o12V, 12.0), (s.o5V, 5.0), (s.o3V3, 3.3),
             (s.on12V, -12.0), (s.oPwrGood, 5.0), (s.oPwrFail, 0.1),
             (s.oYesNoFan, True)))
        t.sw_on.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o12V, 12.0), (s.o5V, 5.0), (s.o3V3, 3.3),
             (s.on12V, -12.0), (s.oPwrGood, 5.0), (s.oPwrFail, 0.1)))
        t.full_load.run()

    def _step_ocp(self):
        """Measure OCP points."""
        # drop back to minimum loads
        for dcl, current in (
                (d.dcl_5Vsb, 0.0), (d.dcl_24V, 0.5), (d.dcl_12V, 0.5),
                (d.dcl_5V, 0.5), (d.dcl_3V3, 0.0)):
            dcl.output(current)
        # 24V OCP
        self.fifo_push(((s.o24V, (24.1, ) * 15 + (22.0, ), ), ))
        d.dcl_24V.binary(0.0, 17.5, 5.0)
        m.ramp_24Vocp.measure()
        d.dcl_24V.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 12V OCP
        self.fifo_push(((s.o12V, (12.1, ) * 15 + (11.0, ), ), ))
        d.dcl_12V.binary(0.0, 19.5, 1.0)
        m.ramp_12Vocp.measure()
        d.dcl_12V.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 5V OCP
        self.fifo_push(((s.o5V, (5.1, ) * 15 + (4.0, ), ), ))
        d.dcl_5V.binary(0.0, 19.5, 1.0)
        m.ramp_5Vocp.measure()
        d.dcl_5V.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 3V3 OCP
        self.fifo_push(((s.o3V3, (3.3, ) * 15 + (3.0, ), ), ))
        d.dcl_3V3.binary(0.0, 16.5, 5.0)
        m.ramp_3V3ocp.measure()
        d.dcl_3V3.output(0.5)
        t.restart.run()
        if not self.running:
            return
        # 5Vsb OCP
        self.fifo_push(((s.o5Vsb, (5.1, ) * 10 + (4.0, ), ), ))
        d.dcl_5Vsb.binary(0.0, 2.1, 1.0)
        m.ramp_5Vsbocp.measure()
        d.dcl_5Vsb.output(0.0)
        t.restart.run()

    def _step_power_fail(self):
        """Switch off unit, measure."""
        self.fifo_push(((s.oPwrFail, 5.05), ))
        t.pwr_fail.run()
