#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UNI-750 Final Test Program."""

import sensor
import tester
from tester.devlogical import *
from tester.measure import *


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        # This DC Source drives the Remote AC Switch
        self.dcs_PwrOn = dcsource.DCSource(devices['DCS1'])
        self.dcl_24V = dcload.DCLoad(devices['DCL1'])
        self.dcl_15V = dcload.DCLoad(devices['DCL2'])
        self.dcl_12V = dcload.DCLoad(devices['DCL3'])
        self.dcl_5V = dcload.DCLoad(devices['DCL4'])
        self.dcl_3V3 = dcload.DCLoad(devices['DCL5'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_PwrOn.output(0.0, output=False)
        for ld in (self.dcl_24V, self.dcl_15V, self.dcl_12V,
                   self.dcl_5V, self.dcl_3V3):
            ld.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oAcUnsw = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self.oAcSw = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.1)
        self.o24V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o15V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.001)
        self.o5Vi = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self.oPGood = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.01)
        self.oYesNoFan = sensor.YesNo(
            message=tester.translate('uni750_final', 'IsFanOn?'),
            caption=tester.translate('uni750_final', 'capFan'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_AcUnsw = Measurement(limits['AcUnsw'], sense.oAcUnsw)
        self.dmm_AcSwOff = Measurement(limits['AcSwOff'], sense.oAcSw)
        self.dmm_AcSwOn = Measurement(limits['AcSwOn'], sense.oAcSw)
        self.dmm_24V = Measurement(limits['24V'], sense.o24V)
        self.dmm_24Vfl = Measurement(limits['24Vfl'], sense.o24V)
        self.dmm_15V = Measurement(limits['15V'], sense.o15V)
        self.dmm_12V = Measurement(limits['12V'], sense.o12V)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_3V3 = Measurement(limits['3.3V'], sense.o3V3)
        self.dmm_5Vi = Measurement(limits['5Vi'], sense.o5Vi)
        self.dmm_PGood = Measurement(limits['PGood'], sense.oPGood)
        self.ui_YesNoFan = Measurement(limits['Notify'], sense.oYesNoFan)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 240Vac, measure.
        acs = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = MeasureSubStep((m.dmm_AcUnsw, m.dmm_AcSwOff, ), timeout=5)
        self.pwr_up = Step((acs, msr))
        # PowerOn: Set min load, switch on, measure.
        ld = LoadSubStep(
            ((d.dcl_24V, 3.0), (d.dcl_15V, 1.0), (d.dcl_12V, 2.0),
             (d.dcl_5V, 1.0), (d.dcl_3V3, 1.0)), output=True)
        dcs = DcSubStep(setting=((d.dcs_PwrOn, 12.0), ), output=True)
        msr = MeasureSubStep(
            (m.dmm_AcSwOn, m.ui_YesNoFan, m.dmm_24V, m.dmm_15V, m.dmm_12V,
             m.dmm_5V, m.dmm_3V3, m.dmm_5Vi, m.dmm_PGood, ), timeout=5)
        self.pwr_on = Step((ld, dcs, msr))
        # Full Load: Apply full load, measure.
        ld = LoadSubStep(
            ((d.dcl_24V, 13.5), (d.dcl_15V, 7.5), (d.dcl_12V, 20.0),
             (d.dcl_5V, 10.0), (d.dcl_3V3, 5.0)))
        msr = MeasureSubStep(
            (m.dmm_24V, m.dmm_15V, m.dmm_12V, m.dmm_5V, m.dmm_3V3, m.dmm_5Vi,
             m.dmm_PGood, ), timeout=5)
        self.full_load = Step((ld, msr))
