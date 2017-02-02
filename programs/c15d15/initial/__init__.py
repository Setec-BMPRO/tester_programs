#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Initial Test Program."""

import logging
import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """C15D-15 Initial Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Charging', self._step_charging),
            )
        # Set the Test Sequence in my base instance
        super().__init__(sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self, parameter):
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

    def _step_power_up(self):
        """Power up."""
        self.fifo_push(
            ((s.vin, 30.0), (s.vcc, 13.0), (s.vout, 15.5),
             (s.led_green, 10.0), (s.led_yellow, 0.2), ))

        d.dcl.output(0.0, output=True)
        d.dcs_input.output(limit.VIN_SET, output=True)
        tester.MeasureGroup(
            (m.dmm_vin, m.dmm_vcc, m.dmm_vout_nl, m.dmm_green_on,
             m.dmm_yellow_off, ), timeout=5)

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.vout, (15.5, ) * 22 + (13.5, ), ), ))

        m.ramp_ocp.measure()
        d.dcl.output(0.0)

    def _step_charging(self):
        """Load into OCP for charging check."""
        self.fifo_push(
            ((s.vout, (13.5, 15.5, )),
             (s.led_green, 10.0), (s.led_yellow, 10.0), ))

        d.rla_load.set_on()
        tester.MeasureGroup(
            (m.dmm_vout_ocp, m.dmm_green_on, m.dmm_yellow_on, ),
            timeout=5)
        d.rla_load.set_off()
        tester.MeasureGroup((m.dmm_vout_nl, ), timeout=5)
