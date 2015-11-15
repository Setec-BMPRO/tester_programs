#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Final Test Program.

        Logical Devices
        Sensors
        Measurements

"""
import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oVbat = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_vbat = Measurement(limits['Vbat'], sense.oVbat)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:  Apply input AC, measure.
        acs1 = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=1.0)
        msr1 = MeasureSubStep((m.dmm_vbat, ), timeout=10)
        self.pwr_up = Step((acs1, msr1))
