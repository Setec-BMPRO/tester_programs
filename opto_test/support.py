#!/usr/bin/env python3
"""Opto Test Program.

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
        self.dcs_vin = dcsource.DCSource(devices['DCS1'])
        self.dcs_vout = dcsource.DCSource(devices['DCS2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_vin, self.dcs_vout):
            dcs.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits
           @param trek2 Trek2 ARM console driver

        """
        dmm = logical_devices.dmm

        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:
        dcs1 = DcSubStep(
            setting=((d.dcs_Vcom, 12.0), (d.dcs_Vin, 12.75)), output=True)
        msr1 = MeasureSubStep((m.dmm_Vin, m.dmm_3V3), timeout=5)
        self.pwr_up = Step((dcs1, msr1, ))
