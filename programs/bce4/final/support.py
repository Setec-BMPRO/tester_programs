#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE4 Final Test Program."""

import time
import sensor
import tester
from tester.devlogical import *
from tester.measure import *


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = tester.devlogical.dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcs_10Vfixture = dcsource.DCSource(devices['DCS1'])
        self.dcl_Vout = dcload.DCLoad(devices['DCL1'])
        self.dcl_Vbat = dcload.DCLoad(devices['DCL2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_10Vfixture.output(0.0, output=False)
        self.dcl_Vout.output(5.0, True)
        time.sleep(0.5)
        for dcl in (self.dcl_Vout, self.dcl_Vbat):
            dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oVout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oAlarm = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        ocp_start, ocp_stop = limits['OCPramp'].limit
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Vout, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)
        self.oDropout = sensor.Ramp(
            stimulus=logical_devices.acsource, sensor=self.oVout,
            detect_limit=(limits['InDropout'], ),
            start=185.0, stop=150.0, step=-0.5, delay=0.1, reset=False)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_VoutNL = Measurement(limits['VoutNL'], sense.oVout)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_AlarmOpen = Measurement(limits['AlarmOpen'], sense.oAlarm)
        self.dmm_AlarmClosed = Measurement(limits['AlarmClosed'], sense.oAlarm)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.dropout = Measurement(limits['Dropout'], sense.oDropout)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements, limits):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # PowerUp: 185Vac, measure, 240Vac, measure.
        dc = DcSubStep(((d.dcs_10Vfixture, 10.0), ))
        ld = LoadSubStep(((d.dcl_Vout, 0.1), (d.dcl_Vbat, 0.0)), output=True)
        msr1 = MeasureSubStep((m.dmm_AlarmClosed, ), timeout=5)
        acs1 = AcSubStep(acs=d.acsource, voltage=185.0, output=True, delay=0.5)
        msr2 = MeasureSubStep((m.dmm_VoutNL, ), timeout=5)
        acs2 = AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr3 = MeasureSubStep(
            (m.dmm_VoutNL, m.dmm_Vbat, m.dmm_AlarmOpen), timeout=5)
        self.power_up = Step((dc, msr1, ld, acs1, msr2, acs2, msr3))

        # Full Load: load, measure.
        ld = LoadSubStep(
            ((d.dcl_Vout, limits['FullLoad'].limit), (d.dcl_Vbat, 0.1)))
        msr1 = MeasureSubStep((m.dmm_Vout, m.dmm_Vbat), timeout=5)
        self.full_load = Step((ld, msr1))

        # Low Mains: 180Vac, measure.
        acs1 = AcSubStep(acs=d.acsource, voltage=185.0, delay=0.5)
        msr1 = MeasureSubStep((m.dmm_Vout, m.dropout, ))
        self.low_mains = Step((acs1, msr1))
