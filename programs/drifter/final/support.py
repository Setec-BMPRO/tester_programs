#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Final Test Program."""

import tester
import sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_Isense = tester.DCSource(devices['DCS1'])
        self.dcs_12V = tester.DCSource(devices['DCS2'])
        self.dcs_Level = tester.DCSource(devices['DCS3'])

    def reset(self):
        """Reset instruments."""
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
            message=tester.translate('drifter_final', 'AreSegmentsOn?'),
            caption=tester.translate('drifter_final', 'capSegments'))
        self.oYesNoBklight = sensor.YesNo(
            message=tester.translate('drifter_final', 'IsBacklightOk?'),
            caption=tester.translate('drifter_final', 'capBacklight'))
        self.oYesNoDisplay = sensor.YesNo(
            message=tester.translate('drifter_final', 'IsDisplayOk?'),
            caption=tester.translate('drifter_final', 'capDisplay'))
        self.oNotifySwOff = sensor.Notify(
            message=tester.translate('drifter_final', 'msgSwitchOff'),
            caption=tester.translate('drifter_final', 'capSwitchOff'))
        self.oNotifySwOn = sensor.Notify(
            message=tester.translate('drifter_final', 'msgSwitchOn'),
            caption=tester.translate('drifter_final', 'capSwitchOn'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
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
        self.displ_check = tester.Step((
            tester.DcSubStep(
                setting=((d.dcs_Isense, 0.2), ), output=True, delay=0.5),
            tester.DcSubStep(
                setting=((d.dcs_12V, 12.0), ), output=True, delay=5),
            tester.MeasureSubStep(
                (m.ui_YesNoSeg, m.ui_YesNoBklight, )),
            tester.DcSubStep(
                setting=((d.dcs_Isense, 0.0), (d.dcs_12V, 0.0), ),
                output=False, delay=1),
            tester.DcSubStep(
                setting=((d.dcs_12V, 12.0), ), output=True, delay=5),
            tester.MeasureSubStep((m.ui_YesNoDisplay, )),
            ))
