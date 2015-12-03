#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Final Test Program."""

import sensor
import tester
from tester.devlogical import *
from tester.measure import *

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcs_Input = dcsource.DCSource(devices['DCS1'])
        self.dcl_Output = dcload.DCLoad(devices['DCL1'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Source
        self.dcs_Input.output(0.0, False)
        # Switch off DC Load
        self.dcl_Output.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.o20V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=translate('_2040_final', 'IsPowerLedGreen?'),
            caption=translate('_2040_final', 'capPowerLed'))
        self.oYesNoDCOff = sensor.YesNo(
            message=translate('_2040_final', 'IsDcRedLedOff?'),
            caption=translate('_2040_final', 'capDcLed'))
        self.oYesNoDCOn = sensor.YesNo(
            message=translate('_2040_final', 'IsDcRedLedOn?'),
            caption=translate('_2040_final', 'capDcLed'))
        self.oYesNoACOff = sensor.YesNo(
            message=translate('_2040_final', 'IsAcRedLedOff?'),
            caption=translate('_2040_final', 'capAcLed'))
        self.oYesNoACOn = sensor.YesNo(
            message=translate('_2040_final', 'IsAcRedLedOn?'),
            caption=translate('_2040_final', 'capAcLed'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_20V = Measurement(limits['20V'], sense.o20V)
        self.dmm_20Vload = Measurement(limits['20Vload'], sense.o20V)
        self.dmm_20Voff = Measurement(limits['20Voff'], sense.o20V)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoDCOff = Measurement(limits['Notify'], sense.oYesNoDCOff)
        self.ui_YesNoDCOn = Measurement(limits['Notify'], sense.oYesNoDCOn)
        self.ui_YesNoACOff = Measurement(limits['Notify'], sense.oYesNoACOff)
        self.ui_YesNoACOn = Measurement(limits['Notify'], sense.oYesNoACOn)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # DCPowerOn: Apply DC Input, measure.
        dcs1 = DcSubStep(setting=((d.dcs_Input, 10.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_20V, m.ui_YesNoGreen, ), timeout=5)
        dcs2 = DcSubStep(setting=((d.dcs_Input, 35.0), ))
        msr2 = MeasureSubStep((m.dmm_20V, ), timeout=5)
        self.dcpwr_on = Step((dcs1, msr1, dcs2, msr2))

        # DCLoad: Full load, measure, discharge, power off.
        ld = LoadSubStep(((d.dcl_Output, 2.0),), output=True)
        msr = MeasureSubStep((m.dmm_20Vload, m.ui_YesNoDCOff, ), timeout=5)
        dcs = DcSubStep(setting=((d.dcs_Input, 0.0), ), output=False, delay=5)
        self.full_load = Step((ld, msr, dcs))

        # ACPowerOn: Apply AC Input, measure.
        ld = LoadSubStep(((d.dcl_Output, 0.0),))
        acs = AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = MeasureSubStep((m.dmm_20V, ), timeout=5)
        self.acpwr_on = Step((ld, acs, msr))

        # ACLoad: Peak load, measure, shutdown.
        ld1 = LoadSubStep(((d.dcl_Output, 3.5),))
        msr1 = MeasureSubStep((m.dmm_20Vload, m.ui_YesNoACOff, ), timeout=5)
        ld2 = LoadSubStep(((d.dcl_Output, 4.05),))
        msr2 = MeasureSubStep((m.dmm_20Voff, m.ui_YesNoACOn, ), timeout=5)
        self.peak_load = Step((ld1, msr1, ld2, msr2))

        # Recover: AC off, load off, AC on.
        acs1 = AcSubStep(acs=d.acsource, voltage=0.0, delay=0.5)
        msr1 = MeasureSubStep((m.dmm_20Voff, ), timeout=5)
        ld = LoadSubStep(((d.dcl_Output, 0.0),))
        acs2 = AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr2 = MeasureSubStep((m.dmm_20V, ), timeout=5)
        self.recover = Step((acs1, msr1, ld, acs2, msr2))
