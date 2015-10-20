#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Final Test Program."""

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
        self.dcs_Isense = dcsource.DCSource(devices['DCS1'])
        self.dcs_12V = dcsource.DCSource(devices['DCS2'])
        self.dcs_Level = dcsource.DCSource(devices['DCS3'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_Isense, self.dcs_12V, self.dcs_Level):
            dcs.output(0.0, output=False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oWaterPump = sensor.Vdc(dmm, high=1, low=2, rng=100, res=0.1)
        self.oBattSw = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self.oUSB5V = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.oYesNoSeg = sensor.YesNo(
            message=translate('drifter_final', 'AreSegmentsOn?'),
            caption=translate('drifter_final', 'capSegments'))
        self.oYesNoBklight = sensor.YesNo(
            message=translate('drifter_final', 'IsBacklightOk?'),
            caption=translate('drifter_final', 'capBacklight'))
        self.oYesNoDisplay = sensor.YesNo(
            message=translate('drifter_final', 'IsDisplayOk?'),
            caption=translate('drifter_final', 'capDisplay'))
        self.oNotifySwOff = sensor.Notify(
            message=translate('drifter_final', 'msgSwitchOff'),
            caption=translate('drifter_final', 'capSwitchOff'))
        self.oNotifySwOn = sensor.Notify(
            message=translate('drifter_final', 'msgSwitchOn'),
            caption=translate('drifter_final', 'capSwitchOn'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_PumpOff = Measurement(
            limits['SwOff'], sense.oWaterPump)
        self.dmm_PumpOn = Measurement(
            limits['SwOn'], sense.oWaterPump)
        self.dmm_BattDisconn = Measurement(
            limits['SwOff'], sense.oBattSw)
        self.dmm_BattConnect = Measurement(
            limits['SwOn'], sense.oBattSw)
        self.dmm_USB5V = Measurement(
            limits['USB5V'], sense.oUSB5V)
        self.ui_YesNoSeg = Measurement(
            limits['Notify'], sense.oYesNoSeg)
        self.ui_YesNoBklight = Measurement(
            limits['Notify'], sense.oYesNoBklight)
        self.ui_YesNoDisplay = Measurement(
            limits['Notify'], sense.oYesNoDisplay)
        self.ui_NotifySwOff = Measurement(
            limits['Notify'], sense.oNotifySwOff)
        self.ui_NotifySwOn = Measurement(
            limits['Notify'], sense.oNotifySwOn)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # DisplayCheck: Apply power, check display.
        dcs1 = DcSubStep(
            setting=((d.dcs_Isense, 0.2), ), output=True, delay=0.5)
        dcs2 = DcSubStep(
            setting=((d.dcs_12V, 12.0), ), output=True, delay=5)
        msr1 = MeasureSubStep(
            (m.ui_YesNoSeg, m.ui_YesNoBklight, ))
        dcs3 = DcSubStep(
            setting=((d.dcs_Isense, 0.0), (d.dcs_12V, 0.0), ),
            output=False, delay=1)
        dcs4 = DcSubStep(
            setting=((d.dcs_12V, 12.0), ), output=True, delay=5)
        msr2 = MeasureSubStep((m.ui_YesNoDisplay, ))
        self.displ_check = Step((dcs1, dcs2, msr1, dcs3, dcs4, msr2))
