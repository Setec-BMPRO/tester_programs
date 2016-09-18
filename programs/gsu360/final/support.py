#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSU360-1TA Final Test Program."""

import time
import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_24V = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_24V.output(5.0, True)
        time.sleep(20.0)    # Allow time to discharge
        self.dcl_24V.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
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
        Measurement = tester.Measurement
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
        ld = tester.LoadSubStep(((d.dcl_24V, 0.5),), output=True)
        acs = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = tester.MeasureSubStep((m.dmm_24V, m.ui_YesNoGreen), timeout=5)
        self.pwr_up = tester.SubStep((ld, acs, msr))
        # Full Load: measure, 110Vac, measure, 240Vac.
        msr1 = tester.MeasureSubStep((m.dmm_24V, ), timeout=5)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=110.0)
        msr2 = tester.MeasureSubStep((m.dmm_24V, ), timeout=5)
        acs2 = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        self.full_load = tester.SubStep((msr1, acs1, msr2, acs2))
