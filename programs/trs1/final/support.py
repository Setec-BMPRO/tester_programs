#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trs1 Final Test Program."""

import sensor
import tester
from tester.devlogical import *
from tester.measure import *

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dcs_Vin = dcsource.DCSource(devices['DCS1'])
        self.dcl = dcload.DCLoad(devices['DCL1'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_Vin, ):
            dcs.output(0.0, False)
        self.dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oBrake = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.01)
        self.oLight = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self.oRemote = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.01)
        self.oNotifyPinOut = sensor.Notify(
            message=translate('trs1_final', 'msgPinOut'),
            caption=translate('trs1_final', 'capPinOut'))
        self.oYesNoGreen = sensor.YesNo(
            message=translate('trs1_final', 'IsLedGreen?'),
            caption=translate('trs1_final', 'capLedGreen'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_brakeoff = Measurement(limits['BrakeOff'], sense.oBrake)
        self.dmm_brakeon = Measurement(limits['BrakeOn'], sense.oBrake)
        self.dmm_lightoff = Measurement(limits['LightOff'], sense.oLight)
        self.dmm_lighton = Measurement(limits['LightOn'], sense.oLight)
        self.dmm_remoteoff = Measurement(limits['BrakeOff'], sense.oRemote)
        self.dmm_remoteon = Measurement(limits['BrakeOn'], sense.oRemote)
        self.ui_NotifyPinOut = Measurement(
            limits['Notify'], sense.oNotifyPinOut)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:
        dcs1 = DcSubStep(setting=((d.dcs_Vin, 12.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_brakeoff, m.dmm_lightoff, m.dmm_remoteoff), timeout=5)
        self.pwr_up = Step((dcs1, msr1, ))
        # BreakAway:
        ld1 = LoadSubStep(((d.dcl, 1.0), ), output=True)
        msr1 = MeasureSubStep((m.ui_NotifyPinOut, m.dmm_brakeon, m.dmm_lighton,
                              m.dmm_remoteon, m.ui_YesNoGreen), timeout=5)
        self.brkaway = Step((ld1, msr1, ))
