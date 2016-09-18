#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMU750-70 Final Test Program."""

import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        dcl1 = tester.DCLoad(devices['DCL1'])
        dcl2 = tester.DCLoad(devices['DCL2'])
        dcl3 = tester.DCLoad(devices['DCL3'])
        dcl4 = tester.DCLoad(devices['DCL4'])
        self.dcl = tester.DCLoadParallel(
            ((dcl1, 1), (dcl2, 1), (dcl3, 1), (dcl4, 1)))

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        translate = tester.translate
        self.o70V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self.oYesNoFan = sensor.YesNo(
            message=translate('smu75070_final', 'IsFanOn?'),
            caption=translate('smu75070_final', 'capFanOn'))
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.o70V,
            detect_limit=(limits['inOCP'], ),
            start=11.3, stop=11.8, step=0.01, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_70Von = Measurement(limits['70VOn'], sense.o70V)
        self.dmm_70Voff = Measurement(limits['70VOff'], sense.o70V)
        self.ui_YesNoFan = Measurement(limits['Notify'], sense.oYesNoFan)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Min load, 240Vac, measure.
        ld1 = tester.LoadSubStep(((d.dcl, 0.0), ), output=True)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=2.0)
        msr1 = tester.MeasureSubStep((m.dmm_70Von, m.ui_YesNoFan,), timeout=5)
        self.pwr_up = tester.SubStep((ld1, acs1, msr1))
        # Full Load: Full load, measure.
        ld1 = tester.LoadSubStep( ((d.dcl, 11.2), ), delay=1)
        msr1 = tester.MeasureSubStep((m.dmm_70Von, ), timeout=5)
        self.full_load = tester.SubStep((ld1, msr1))
        # Shutdown: Overload, restart, measure.
        ld1 = tester.LoadSubStep( ((d.dcl, 11.9), ))
        msr1 = tester.MeasureSubStep((m.dmm_70Voff, ), timeout=5)
        ld2 = tester.LoadSubStep( ((d.dcl, 0.0), ), delay=2)
        msr2 = tester.MeasureSubStep((m.dmm_70Von, ), timeout=10)
        self.shdn = tester.SubStep((ld1, msr1, ld2, msr2))
