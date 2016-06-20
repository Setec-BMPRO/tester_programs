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
            ('TunnelOpen', self._step_tunnel_open, None, True),
            ('Display', self._step_display, None, True),
            ('TestAllTanksA', self._step_tanksA, None, True),
            ('TestAllTanksB', self._step_tanksB, None, True),
            ('TestAllTanksC', self._step_tanksC, None, True),
            ('TestAllTanksD', self._step_tanksD, None, True),
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
        global d, s, m
        d = support.LogicalDevices(self._devices, self._fifo)
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
        if self._fifo:
            d.tunnel.port.puts('0 ECHO -> \r\n> ', preflush=1)
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('0x10000000\r\n')
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('RRC,32,3,3,0,16,1\r\n')
        d.trek2_puts('0x10000000')
        d.trek2_puts('')

        d.trek2.open()
        d.trek2.testmode(True)

    def _step_display(self):
        """Display tests."""
        for sens in (s.oYesNoSeg, s.oYesNoBklight, ):
            self.fifo_push(((sens, True), ))
        d.trek2_puts('0x10000000')
        d.trek2_puts('')

        tester.MeasureGroup((m.ui_YesNoSeg, m.ui_YesNoBklight, ))
        d.trek2.testmode(False)

    def _step_tanksA(self):
        """Tank tests - Empty."""
        for sens in (s.tank1, s.tank2, s.tank3, s.tank4, ):
            self.fifo_push(((sens, 1), ))
        d.trek2_puts('')
        d.trek2_puts('')

        d.trek2['CONFIG'] = 0x7E00      # Enable all 4 tanks
        d.trek2['TANK_SPEED'] = 0.1     # Change update interval
        time.sleep(2)
        tester.MeasureGroup(m.level1)

    def _step_tanksB(self):
        for sens in (s.tank1, s.tank2, s.tank3, s.tank4, ):
            self.fifo_push(((sens, 2), ))

        """Tank tests - 1 sensor."""
        d.rla_s1.set_on()
        time.sleep(2)
        tester.MeasureGroup(m.level2)

    def _step_tanksC(self):
        """Tank tests - 2 sensors."""
        for sens in (s.tank1, s.tank2, s.tank3, s.tank4, ):
            self.fifo_push(((sens, 3), ))

        d.rla_s2.set_on()
        time.sleep(2)
        tester.MeasureGroup(m.level3)

    def _step_tanksD(self):
        """Tank tests - 3 sensors."""
        for sens in (s.tank1, s.tank2, s.tank3, s.tank4, ):
            self.fifo_push(((sens, 4), ))

        d.rla_s3.set_on()
        time.sleep(2)
        tester.MeasureGroup(m.level4)
