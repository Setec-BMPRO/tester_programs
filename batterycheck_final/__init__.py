#!/usr/bin/env python3
"""BatteryCheck Final Test Program."""

import os
import logging

import tester
import share.bcheck

from . import support
from . import limit

LIMIT_DATA = limit.DATA

_BT_PORT = {'posix': '/dev/ttyUSB0',
            'nt': r'\\.\COM9',
            }[os.name]

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
        self._bt = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self._bt = share.bcheck.BtCheck(port=_BT_PORT)
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._bt.btclose()
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
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
        self.fifo_push(
            ((s.oMirBT, (True,) * 3), (s.oMirSwVer, ('1.4.3334',)), ))

        self._logger.debug('Testing Bluetooth Serial: "%s"', self._sernum)
        _paired = False
        if self._fifo:
            m.BTscan.measure()
            m.BTpair.measure()
            m.SerNumARM.measure()
            m.SwVerARM.measure()
        else:
            self._bt.btopen()
            try:
                _matched = self._bt.btscan(self._sernum)
                s.oMirBT.store(_matched)
                m.BTscan.measure()
                _paired = self._bt.btpair()
                s.oMirBT.store(_paired)
                m.BTpair.measure()
                self._bt.btcon()
                _info = self._bt.btinfo()
                s.oMirBT.store(_info['SerialID'] == self._sernum)
                m.SerNumARM.measure()
                s.oMirSwVer.store((_info['SoftwareVersion'], ))
                m.SwVerARM.measure()
            except Exception as err:
                self._logger.debug('Exception raised: %s', repr(err))
            finally:
                if _paired:
                    self._bt.btesc()
                    self._bt.btunpair()
