#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GENIUS-II and GENIUS-II-H Initial Test Program."""

import sensor
import tester

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_Vbat = tester.DCSource(devices['DCS1'])
        dcl_vout = tester.DCLoad(devices['DCL1'])
        dcl_vbat = tester.DCLoad(devices['DCL3'])
        self.dcl = tester.DCLoadParallel(((dcl_vout, 29), (dcl_vbat, 14)))
        self.dclh = tester.DCLoadParallel(((dcl_vout, 5), (dcl_vbat, 30)))
        self.rla_RemoteSw = tester.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_Vbat.output(0.0, False)
        self.dcl.output(0.0)
        self.rla_RemoteSw.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oVout = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: 240Vac, wait for Vout to start, measure.
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=240.0, output=True)
        msr1 = tester.MeasureSubStep((m.dmm_Vout, m.dmm_Vbat), timeout=10)
        self.pwrup = tester.SubStep((acs1, msr1))
