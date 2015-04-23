#!/usr/bin/env python3
"""BCE282-12/24 Final Program."""

import time

import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor
translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcl_Vout = dcload.DCLoad(devices['DCL1'])
        self.dcl_Vbat = dcload.DCLoad(devices['DCL2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Discharge unit
        self.dcl_Vout.output(10.0, True)
        time.sleep(0.5)
        # Switch off DC Loads
        for dcl in (self.dcl_Vout, self.dcl_Vbat):
            dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oVout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oAlarm = sensor.Res(dmm, high=5, low=3, rng=100000, res=1)
        tester.TranslationContext = 'bce282_final'
        self.oYesNoGreen = sensor.YesNo(
            message=translate('IsGreenFlash?'),
            caption=translate('capLedGreen'))
        ocp_start, ocp_stop = limits['OCPrampLoad'].limit
        self.oOCPLoad = sensor.Ramp(
            stimulus=logical_devices.dcl_Vout, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)
        ocp_start, ocp_stop = limits['OCPrampBatt'].limit
        self.oOCPBatt = sensor.Ramp(
            stimulus=logical_devices.dcl_Vbat, sensor=self.oVbat,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_VoutNL = Measurement(limits['VoutNL'], sense.oVout)
        self.dmm_VbatNL = Measurement(limits['VbatNL'], sense.oVbat)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_AlarmClosed = Measurement(limits['AlarmClosed'], sense.oAlarm)
        self.dmm_AlarmOpen = Measurement(limits['AlarmOpen'], sense.oAlarm)
        self.ramp_OCPLoad = Measurement(limits['OCPLoad'], sense.oOCPLoad)
        self.ramp_OCPBatt = Measurement(limits['OCPBatt'], sense.oOCPBatt)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements, limits):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: 200Vac, measure, 240Vac, measure.
        msr1 = MeasureSubStep((m.dmm_AlarmClosed, ), timeout=5)
        acs1 = AcSubStep(
            acs=d.acsource, voltage=200.0, output=True, delay=0.5)
        ld = LoadSubStep(
            ((d.dcl_Vout, 0.1), (d.dcl_Vbat, 0.0)), output=True)
        msr2 = MeasureSubStep((m.dmm_VoutNL, ), timeout=5)
        acs2 = AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr3 = MeasureSubStep(
            (m.dmm_VoutNL, m.dmm_VbatNL, m.dmm_AlarmOpen), timeout=5)
        self.power_up = Step((msr1, acs1, ld, msr2, acs2, msr3))
        # Full Load: load, measure.
        ld1 = LoadSubStep(((d.dcl_Vbat, 0.5), ))
        msr1 = MeasureSubStep((m.ui_YesNoGreen, ), timeout=5)
        ld2 = LoadSubStep(
            ((d.dcl_Vbat, 0.0), (d.dcl_Vout, limits['FullLoad'].limit)))
        msr2 = MeasureSubStep((m.dmm_Vout, m.dmm_Vbat), timeout=5)
        self.full_load = Step((ld1, msr1, ld2, msr2))
