#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STxx-III Final Test Program."""

import logging
import time
import tester
from . import support
from . import limit

FIN20_LIMIT = limit.DATA20     # ST20 limits
FIN35_LIMIT = limit.DATA35     # ST35 limits

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Final(tester.TestSequence):

    """STxx-III Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FuseLabel', self._step_label, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('Battery', self._step_battery, None, True),
            ('LoadOCP', self._step_load_ocp, None, True),
            ('BattOCP', self._step_batt_ocp, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # It is a ST35 if FullLoad current > 25A
        self._fullload = test_limits['FullLoad'].limit
        self._is35 = (self._fullload > 25)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
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

    def _step_label(self):
        """Check Fuse Label."""
        barcode = 'ST35-III' if self._is35 else 'ST20-III'
        self.fifo_push(((s.oBarcode, (barcode, )), ))
        m.barcode.measure()

    def _step_power_up(self):
        """Power up unit."""
        self.fifo_push(
            ((s.oLoad, 14.0), (s.oFuse1, 13.65), (s.oFuse2, 13.65),
             (s.oFuse3, 13.65), (s.oFuse4, 13.65), (s.oFuse5, 13.65),
             (s.oFuse6, 13.65), (s.oFuse7, 13.65), (s.oFuse8, 13.65),
             (s.oBatt, 13.65), (s.oYesNoOrGr, True), ))
        t.power_up.run()

    def _step_battery(self):
        """Battery checks."""
        self.fifo_push(
            ((s.oBatt, (0.4, 13.65)), (s.oYesNoRedOn, True),
             (s.oYesNoRedOff, True), ))
        t.battery.run()

    def _step_load_ocp(self):
        """Measure Load OCP point."""
        self.fifo_push(((s.oLoad, (13.5, ) * 15 + (11.0, 0.5, 13.6), ), ))
        m.ramp_LoadOCP.measure()
        d.dcl_Load.output(self._fullload * 1.30)
        m.dmm_Overload.measure(timeout=5)
        d.dcl_Load.output(0.0)
        m.dmm_Load.measure(timeout=10)
        time.sleep(1)

    def _step_batt_ocp(self):
        """Measure Batt OCP point."""
        self.fifo_push(((s.oBatt, (13.5, ) * 12 + (11.0, 13.6, ), ), ))
        m.ramp_BattOCP.measure()
        d.dcl_Batt.output(0.1)
        m.dmm_Batt.measure(timeout=5)
