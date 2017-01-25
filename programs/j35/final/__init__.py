#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""J35 Final Test Program."""

import tester
from share import oldteststep
from . import support
from . import limit

FIN_LIMIT_A = limit.DATA_A
FIN_LIMIT_B = limit.DATA_B
FIN_LIMIT_C = limit.DATA_C


class Final(tester.TestSequence):

    """J35 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True if FIFOs are enabled

        """
        super().__init__(selection, None, fifo)
        self.phydev = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensors = None
        self.meas = None

    def open(self):
        """Prepare for testing."""
        self.logdev = support.LogicalDevices(self.phydev)
        self.sensors = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensors, self.limits)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Load', self._step_load),
            tester.TestStep('OCP', self._step_ocp),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        self.logdev = None
        self.sensors = None
        self.meas = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac and measure output voltage."""
        dev.dcs_photo.output(12.0, True)
        mes.dmm_fanoff.measure(timeout=5)
        dev.acsource.output(240.0, output=True)
        mes.dmm_fanon.measure(timeout=15)
        for load in range(self.limits['LOAD_COUNT'].limit):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.dmm_vouts[load].measure(timeout=5)

    @oldteststep
    def _step_load(self, dev, mes):
        """Test outputs with load."""
        dev.dcl_out.output(0.0,  output=True)
        dev.dcl_out.binary(1.0, self.limits['LOAD_CURRENT'].limit, 5.0)
        for load in range(self.limits['LOAD_COUNT'].limit):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.dmm_vloads[load].measure(timeout=5)

    @oldteststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        mes.ramp_ocp.measure(timeout=5)
