#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Final Test Program."""

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
        self.vload = sensor.Vdc(
            logical_devices.dmm, high=1, low=1, rng=100, res=0.001)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_vload = tester.Measurement(limits['Vload'], sense.vload)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Input AC, measure.
        self.pwrup = tester.SubStep((
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, output=True, delay=1.0),
            tester.MeasureSubStep((m.dmm_vload, ), timeout=10),
            ))
