#!/usr/bin/env python3
"""BatteryCheck Final Test Program."""

import os
import logging

import tester
from share.sim_serial import SimSerial
from share.bluetooth import BtRadio

from . import support
from . import limit

LIMIT_DATA = limit.DATA

_BT_PORT = {'posix': '/dev/ttyUSB0', 'nt': r'\\.\COM9'}[os.name]

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """BatteryCheck Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('TestBlueTooth', self._step_test_bluetooth, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._sernum = None
        self._btport = None
        self._bt = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        # Serial connection to the BT device
        self._btport = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=2, writeTimeout=10)
        # Set port separately, as we don't want it opened yet
        self._btport.setPort(_BT_PORT)
        # BT Radio driver
        self._bt = BtRadio(self._btport)
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def _bt_puts(self,
                 string_data, preflush=0, postflush=0, priority=False):
        """Push string data into the BT buffer only if FIFOs are enabled."""
        if self._fifo:
            self._btport.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._bt.close()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_power_up(self):
        """Power the battery check."""
        self.fifo_push(((s.oSnEntry, ('A1509020010', )), (s.o12V, 12.0), ))
        self._sernum = str(self.uuts[0])
        sn_lim = self._limits['SerNum']
        sn_lim.position_fail = False
        match = (sn_lim == self._sernum)
        sn_lim.position_fail = True
        if not match:   # Display pop-up box to enter serial number.
            result, sernum = m.ui_SnEntry.measure()
            self._sernum = sernum[0]
        t.pwr_up.run()

    def _step_test_bluetooth(self):
        """Test the Bluetooth transmitter function.

        Scan for BT devices and match against serial number.

        """
        self._logger.debug('Testing Bluetooth Serial: "%s"', self._sernum)
        _paired = False
        self._bt_puts('OK\r\n', preflush=2)
        self._bt_puts('OK\r\n', preflush=1)
        self._bt.open()
        self._bt_puts('OK\r\n', preflush=1)
        self._bt_puts('+RDDSRES=112233445566,BCheck A1509020010,2,3\r\n')
        self._bt_puts('+RDDSCNF=0\r\n')
        self._bt.scan(self._sernum)
        s.oMirBT.store(True)
        m.BTscan.measure()
        self._bt_puts('OK\r\n', preflush=1)
        self._bt_puts('+RPCI=\r\n') # Ask for PIN
        self._bt_puts('OK\r\n', preflush=1)
        self._bt_puts('+RUCE=\r\n') # Ask for 6-digit verify
        self._bt_puts('OK\r\n', preflush=1)
        self._bt_puts('+RCCRCNF=500,0000,0\r\n') # Pair response
        self._bt.pair()
        _paired = True
        s.oMirBT.store(_paired)
        m.BTpair.measure()
        self._bt_puts('OK\r\n', preflush=1)
        self._bt.data_mode_enter()
        self._bt_puts(
            '{"jsonrpc": "2.0","id": 8256,'
            '"result": {"HardwareVersion": "2.0",'
            '"SoftwareVersion": "1.4.3334",'
            '"SerialID": "A1509020010"}}', preflush=1)
        _info = self._bt.jsonrpc('GetSystemInfo')
        s.oMirSwVer.store((_info['SoftwareVersion'], ))
        m.SwVerARM.measure()
        s.oMirBT.store(_info['SerialID'] == self._sernum)
        m.SerNumARM.measure()
        if _paired:
            self._bt_puts('OK\r\n', preflush=1)
            self._bt.data_mode_escape()
            self._bt_puts('OK\r\n', preflush=1)
            self._bt_puts('+RDII\r\n')
            self._bt.unpair()
