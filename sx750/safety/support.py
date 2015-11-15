#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Safety Test Program."""

import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.st = safety.SafetyTester(devices['SAF'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        pass


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        st = logical_devices.st
        # Safety Tester sequence and test steps
        self.gnd1 = sensor.STGND(st, step=1, ch=1)
        self.gnd2 = sensor.STGND(st, step=2, ch=2, curr=11)
        self.gnd3 = sensor.STGND(st, step=3, ch=3, curr=11)
        self.acw = sensor.STACW(st, step=4)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.gnd1 = Measurement(limits['gnd'], sense.gnd1)
        self.gnd2 = Measurement(limits['gnd'], sense.gnd2)
        self.gnd3 = Measurement(limits['gnd'], sense.gnd3)
        self.acw = Measurement((limits['arc'], limits['acw']), sense.acw)
