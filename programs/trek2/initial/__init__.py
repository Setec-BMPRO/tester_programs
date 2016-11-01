#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import logging
import time
import tester
import share
from . import support
from . import limit


INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """Trek2 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not fifo),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('CanBus', self._step_canbus),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self.sernum = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices, self.fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        d.dcs_Vcom.output(12.0, output=True)
        time.sleep(2)   # Allow OS to detect the new ports

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        d.dcs_Vcom.output(0.0, output=False)
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(
            ((s.oSnEntry, ('A1526040123', )), (s.oVin, 12.0), (s.o3V3, 3.3), ))

        self._sernum = share.get_sernum(
            self.uuts, self._limits['SerNum'], m.ui_SnEntry)
        d.dcs_Vin.output(limit.VIN_SET, output=True)
        tester.MeasureGroup((m.dmm_Vin, m.dmm_3V3), timeout=5)

    def _step_program(self):
        """Program the ARM device."""
        d.programmer.program()

    def _step_test_arm(self):
        """Test the ARM device."""
        for str in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) + ('success', ) * 2 + ('', ) * 2 +
                (limit.BIN_VERSION, )
                ):
            d.trek2_puts(str)

        d.trek2.open()
        d.rla_reset.pulse(0.1)
        d.trek2.action(None, delay=1.5, expected=2)  # Flush banner
        d.trek2['UNLOCK'] = True
        d.trek2['HW_VER'] = limit.HW_VER
        d.trek2['SER_ID'] = self.sernum
        d.trek2['NVDEFAULT'] = True
        d.trek2['NVWRITE'] = True
        m.trek2_SwVer.measure()

    def _step_canbus(self):
        """Test the Can Bus."""
        for str in ('0x10000000', '', '0x10000000', '', ''):
            d.trek2_puts(str)
        d.trek2_puts('RRQ,16,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.trek2_can_bind.measure(timeout=10)
        d.trek2.can_testmode(True)
        time.sleep(2)   # Let other CAN messages come in...
        # From here, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(limit.CAN_ECHO))
        d.trek2['CAN'] = limit.CAN_ECHO
        echo_reply = d.trek2_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        s.oMirCAN.store(echo_reply)
        m.rx_can.measure()
