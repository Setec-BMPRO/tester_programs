#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Final Test Program."""

import logging
import share
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Final(tester.TestSequence):

    """BatteryCheck Final Test Program."""

    def __init__(self, per_panel, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('TestBlueTooth', self._step_test_bluetooth),
            )
        # Set the Test Sequence in my base instance
        super().__init__(per_panel, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._sernum = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices, self.fifo)
        s = support.Sensors(d)
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
        """Power the battery check."""
        self.fifo_push(((s.oSnEntry, ('A1509020010', )), (s.o12V, 12.0), ))

        self._sernum = share.get_sernum(
            self.uuts, self._limits['SerNum'], m.ui_SnEntry)
        d.dcs_input.output(12.0, output=True)
        m.dmm_12V.measure(timeout=5)

    def _step_test_bluetooth(self):
        """Test the Bluetooth transmitter function.

        Scan for BT devices and match against serial number.

        """
        d.bt_puts('OK\r\n', preflush=2)
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts('+RDDSRES=112233445566,BCheck A1509020010,2,3\r\n')
        d.bt_puts('+RDDSCNF=0\r\n')
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts('+RPCI=\r\n') # Ask for PIN
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts('+RUCE=\r\n') # Ask for 6-digit verify
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts('+RCCRCNF=500,0000,0\r\n') # Pair response
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts(
            '{"jsonrpc": "2.0","id": 8256,'
            '"result": {"HardwareVersion": "2.0",'
            '"SoftwareVersion": "' + limit.ARM_VERSION + '",'
            '"SerialID": "A1509020010"}}\r\n', preflush=1)
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts('OK\r\n', preflush=1)
        d.bt_puts('+RDII\r\n')

        self._logger.debug('Testing Bluetooth Serial: "%s"', self._sernum)
        d.bt.open()
        found = d.bt.scan(self._sernum)
        s.oMirBT.store(found)
        m.BTscan.measure()
        try:
            d.bt.pair()
        except share.BtError:
            _paired = False
        _paired = True
        s.oMirBT.store(_paired)
        m.BTpair.measure()
        d.bt.data_mode_enter()
        _info = d.bt.jsonrpc('GetSystemInfo')
        s.oMirSwVer.store((_info['SoftwareVersion'], ))
        m.SwVerARM.measure()
        s.oMirBT.store(_info['SerialID'] == self._sernum)
        m.SerNumARM.measure()
        d.bt.data_mode_escape()
        d.bt.unpair()
