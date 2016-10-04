#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Final Test Program."""

import logging
import tester
from . import support
from . import limit

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
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Load', self._step_load, True),
            tester.TestStep('OCP', self._step_ocp, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.phydev = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensors = None
        self.meas = None
        self._LOAD_COUNT = self.limits['LOAD_COUNT'].limit
        self._LOAD_CURRENT = self.limits['LOAD_CURRENT'].limit

    def open(self):
        """Prepare for testing."""
        self.logdev = support.LogicalDevices(self.phydev)
        self.sensors = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensors, self.limits)

    def close(self):
        """Finished testing."""
        self.logdev = None
        self.sensors = None
        self.meas = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    def _step_powerup(self):
        """Power-Up the Unit with 240Vac and measure output voltage."""
        dev, mes = self.logdev, self.meas
        dev.dcs_photo.output(12.0, True)
        mes.dmm_fanoff.measure(timeout=5)
        dev.acsource.output(240.0, True)
        mes.dmm_fanon.measure(timeout=12)
        for load in range(self._LOAD_COUNT):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.dmm_vouts[load].measure(timeout=5)

    def _step_load(self):
        """Test outputs with load."""
        dev, mes = self.logdev, self.meas
        dev.dcl_out.binary(1.0, self._LOAD_CURRENT, 5.0)
        for load in range(self._LOAD_COUNT):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.dmm_vloads[load].measure(timeout=5)

    def _step_ocp(self):
        """Test OCP."""
        mes = self.meas
        mes.ramp_ocp.measure(timeout=5)
