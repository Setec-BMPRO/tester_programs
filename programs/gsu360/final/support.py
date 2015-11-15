#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSU360-1TA Final Test Program."""

import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = tester.devlogical.dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcl_24V = dcload.DCLoad(devices['DCL1'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Load
        self.dcl_24V.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.o24V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
# FIXME: Use translations here.
        self.oYesNoGreen = sensor.YesNo(
            message='Is the <b>GREEN POWER SWITCH</b> light <b>ON</b> ?',
            caption='Switch light')
        self.o24Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_24V, sensor=self.o24V,
            detect_limit=(limits['24Vinocp'], ),
            start=15.0, stop=20.5, step=0.1, delay=0.1, reset=False)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_24V = Measurement(limits['24V'], sense.o24V)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ramp_24Vocp = Measurement(limits['24Vocp'], sense.o24Vocp)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 240Vac, measure.
        ld = LoadSubStep(((d.dcl_24V, 0.5),), output=True)
        acs = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = MeasureSubStep((m.dmm_24V, m.ui_YesNoGreen), timeout=5)
        self.pwr_up = Step((ld, acs, msr))
        # Full Load: measure, 110Vac, measure, 240Vac.
        msr1 = MeasureSubStep((m.dmm_24V, ), timeout=5)
        acs1 = AcSubStep(acs=d.acsource, voltage=110.0)
        msr2 = MeasureSubStep((m.dmm_24V, ), timeout=5)
        acs2 = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        self.full_load = Step((msr1, acs1, msr2, acs2))
