#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Initial Test Program for GENIUS-II and GENIUS-II-H."""

import logging
import time
import tester
from share import oldteststep
from . import support
from . import limit

INI_LIMIT = limit.DATA          # GENIUS-II limits
INI_LIMIT_H = limit.DATA_H      # GENIUS-II-H limits


class Initial(tester.TestSequence):

    """GENIUS-II Initial Test Program."""

    def __init__(self, per_panel, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        super().__init__(per_panel, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.phydev = physical_devices
        self.limits = test_limits
        # It is a GENIUS-II-H if BattLoad current > 20A
        self._fullload = test_limits['MaxBattLoad'].limit
        self._isH = (self._fullload > 20)
        self.logdev = None
        self.sensor = None
        self.meas = None
        self.subtest = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self.logdev = support.LogicalDevices(self.phydev)
        self.sensor = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensor, self.limits)
        self.subtest = support.SubTests(self.logdev, self.meas)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('Prepare', self.subtest.prepare.run),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('Aux', self.subtest.aux.run),
            tester.TestStep('PowerUp', self.subtest.pwrup.run),
            tester.TestStep('VoutAdj', self._step_vout_adj),
            tester.TestStep('ShutDown', self.subtest.shdn.run),
            tester.TestStep('OCP', self._step_ocp),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.logdev.reset()

    @oldteststep
    def _step_program(self, dev, mes):
        """Program the board."""
        dev.program_pic.program()
        dev.dcs_vbatctl.output(0.0, False)

    @oldteststep
    def _step_vout_adj(self, dev, mes):
        """Vout adjustment."""
        mes.ui_AdjVout.measure(timeout=5)
        dev.dcl.output(2.0)
        tester.MeasureGroup(
            (mes.dmm_vout, mes.dmm_vbatctl, mes.dmm_vbat, mes.dmm_vdd),
            timeout=5)

    @oldteststep
    def _step_ocp(self, dev, mes):
        """Ramp up load until OCP."""
        # Check for correct model (GENIUS-II/GENIUS-II-H)
        dev.dcl_vbat.binary(0.0, 18.0, 5.0)
        mes.dmm_vbatocp.measure(timeout=2)
        dev.dcl_vbat.output(0.0)
        mes.dmm_vbat.measure(timeout=10)
        time.sleep(2)
        if self._isH:
            dev.dclh.binary(0.0, 32.0, 5.0)
            mes.ramp_OCP_H.measure()
        else:
            dev.dcl.binary(0.0, 32.0, 5.0)
            mes.ramp_OCP.measure()
