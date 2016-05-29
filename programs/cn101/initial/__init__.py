#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Test Program."""

import logging
import time

import tester
from . import support
from . import limit


INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """CN101 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PartCheck', self._step_part_check, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('Program', self._step_program, None, not fifo),
            ('TestArm', self._step_test_arm, None, True),
            ('Awning', self._step_awning, None, True),
            ('TankSense', self._step_tank_sense, None, True),
            ('Bluetooth', self._step_bluetooth, None, True),
            ('CanBus', self._step_canbus, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._sernum = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices, self._fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)
        d.dcs_vcom.output(12.0, output=True)
        time.sleep(5)   # Allow OS to detect the new ports

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        d.dcs_vcom.output(0.0, output=False)
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_part_check(self):
        """Measure Part detection microswitches."""
        self.fifo_push(((s.microsw, 10.0), (s.sw1, 10.0), (s.sw2, 10.0), ))

        tester.MeasureGroup((m.dmm_microsw, m.dmm_sw1, m.dmm_sw2), 5)

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(
            ((s.oSnEntry, ('A1526040123', )), (s.oVin, 8.0), (s.o3V3, 3.3), ))

        self._sernum = m.ui_serialnum.measure().reading1
        d.dcs_vin.output(8.6, output=True)
        tester.MeasureGroup((m.dmm_vin, m.dmm_3v3, ), timeout=5)

    def _step_program(self):
        """Program the ARM device."""
        d.rla_boot.set_on()
        d.rla_reset.pulse(0.1)
        d.programmer.program()
        d.rla_boot.set_off()

    def _step_test_arm(self):
        """Test the ARM device."""
        for str in (('Banner1\r\nBanner2', ) +
                    ('', ) * 5 ):
            d.cn101_puts(str)
        d.cn101_puts(limit.BIN_VERSION, postflush=0)

        d.cn101.open()
        d.rla_reset.pulse(0.1)
        d.cn101.action(None, delay=1.5, expected=2)   # Flush banner
        d.cn101['UNLOCK'] = True
        d.cn101['HW_VER'] = limit.HW_VER
        d.cn101['SER_ID'] = self._sernum
        d.cn101['NVDEFAULT'] = True
        d.cn101['NVWRITE'] = True
        m.cn101_swver.measure()

    def _step_awning(self):
        """Test Awning relay operation."""
        self.fifo_push(((s.oAwnA, (0.0, 11.0)), (s.oAwnB, (0.0, 11.0)), ))

        t.awning.run()

    def _step_tank_sense(self):
        """Activate tank sensors and read."""
        for str in (('', ) + ('5', ) * 4):
            d.cn101_puts(str)

        d.cn101['ADC_SCAN'] = 100
        t.tank.run()

    def _step_bluetooth(self):
        """Test the Bluetooth interface."""
        d.cn101_puts('001EC030BC15', )

        t.reset.run()
        _btmac = m.cn101_btmac.measure().reading1
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', _btmac)
        if self._fifo:
            reply = True
        else:
            self._ble.open()
            reply = self._ble.scan(_btmac)
            self._ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        s.oMirBT.store(reply)
        m.detectBT.measure()

    def _step_canbus(self):
        """Test the CAN interface."""
        for str in ('0x10000000', '', '0x10000000', '', ''):
            d.cn101_puts(str)
        d.cn101_puts('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.cn101_can_bind.measure(timeout=10)
        d.cn101.can_testmode(True)
        # From here on, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(limit.CAN_ECHO))
        d.cn101['CAN'] = limit.CAN_ECHO
        echo_reply = d.cn101_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        s.oMirCAN.store(echo_reply)
        m.cn101_rx_can.measure()
