#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Final Test Program."""

import tester
import sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        self.vbat = sensor.Vdc(
            logical_devices.dmm, high=1, low=1, rng=100, res=0.001)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_vbat = tester.Measurement(limits['Vbat'], sense.vbat)
