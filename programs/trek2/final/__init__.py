#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Test Program."""

import logging
import time
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Final(tester.TestSequence):

    """Trek2 Final Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('TunnelOpen', self._step_tunnel_open),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('TestTanks', self._step_test_tanks),
            )
        # Set the Test Sequence in my base instance
        super().__init__(sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices, self.fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global d, s, m
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        # Switch on the USB hub & Serial ports
        d.dcs_Vcom.output(12.0, output=True)
        d.dcs_Vin.output(12.0, output=True)
        time.sleep(9)           # Wait for CAN binding to finish

    def _step_tunnel_open(self):
        """Open console tunnel."""
        if self.fifo:
            d.tunnel.port.puts('0 ECHO -> \r\n> ', preflush=1)
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('0x10000000\r\n')
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('RRC,32,3,3,0,16,1\r\n')
        d.trek2.puts('0x10000000')
        d.trek2.puts('')

        d.trek2.open()
        d.trek2.testmode(True)

    def _step_display(self):
        """Display tests."""
        for sens in (s.oYesNoSeg, s.oYesNoBklight, ):
            self.fifo_push(((sens, True), ))
        d.trek2.puts('0x10000000')
        d.trek2.puts('')

        tester.MeasureGroup((m.ui_YesNoSeg, m.ui_YesNoBklight, ))
        d.trek2.testmode(False)

    def _step_test_tanks(self):
        """Test all tanks one level at a time."""
        for sens in s.otanks:
            self.fifo_push(((sens, (1, 2, 3, 4)), ))
        d.trek2.puts('')
        d.trek2.puts('')

        d.trek2['CONFIG'] = 0x7E00      # Enable all 4 tanks
        d.trek2['TANK_SPEED'] = 0.1     # Change update interval
        # No sensors - Tanks empty!
        tester.MeasureGroup(m.arm_level1, timeout=12)
        # 1 sensor
        d.rla_s1.set_on()
        tester.MeasureGroup(m.arm_level2, timeout=12)
        # 2 sensors
        d.rla_s2.set_on()
        tester.MeasureGroup(m.arm_level3, timeout=12)
        # 3 sensors
        d.rla_s3.set_on()
        tester.MeasureGroup(m.arm_level4, timeout=12)
