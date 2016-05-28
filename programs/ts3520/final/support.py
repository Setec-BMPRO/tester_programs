#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TS3520 Final Test Program."""

import sensor
import tester
from tester.devlogical import *
from tester.measure import *


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        _dcl_12Va = dcload.DCLoad(devices['DCL1'])
        _dcl_12Vb = dcload.DCLoad(devices['DCL2'])
        self.dcl = dcload.DCLoadParallel(
            ((_dcl_12Va, 12.5), (_dcl_12Vb, 12.5)))

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.o12V_1 = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o12V_2 = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o12V_3 = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.oNotifyStart = sensor.Notify(
            message=tester.translate('ts3520_final', 'RemoveFuseSwitchOn'),
            caption=tester.translate('ts3520_final', 'capSwitchOn'))
        self.oNotifyFuse = sensor.Notify(
            message=tester.translate('ts3520_final', 'ReplaceFuse'),
            caption=tester.translate('ts3520_final', 'capReplaceFuse'))
        self.oNotifyMains = sensor.Notify(
            message=tester.translate('ts3520_final', 'SwitchOff'),
            caption=tester.translate('ts3520_final', 'capSwitchOff'))
        self.oYesNoRed = sensor.YesNo(
            message=tester.translate('ts3520_final', 'IsRedLedOn?'),
            caption=tester.translate('ts3520_final', 'capRedLed'))
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('ts3520_final', 'IsGreenLedOn?'),
            caption=tester.translate('ts3520_final', 'capGreenLed'))
        self.oYesNoOff = sensor.YesNo(
            message=tester.translate('ts3520_final', 'AreAllLightsOff?'),
            caption=tester.translate('ts3520_final', 'capAllOff'))
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.o12V_1,
            detect_limit=(limits['inOCP'], ),
            start=24.5, stop=31.0, step=0.1, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_12Voff = Measurement(limits['12Voff'], sense.o12V_1)
        self.dmm_12V_1 = Measurement(limits['12V'], sense.o12V_1)
        self.dmm_12V_2 = Measurement(limits['12V'], sense.o12V_2)
        self.dmm_12V_3 = Measurement(limits['12V'], sense.o12V_3)
        self.dmm_12Vfl = Measurement(limits['12Vfl'], sense.o12V_1)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.ui_NotifyStart = Measurement(limits['Notify'], sense.oNotifyStart)
        self.ui_NotifyFuse = Measurement(limits['Notify'], sense.oNotifyFuse)
        self.ui_NotifyMains = Measurement(limits['Notify'], sense.oNotifyMains)
        self.ui_YesNoRed = Measurement(limits['Notify'], sense.oYesNoRed)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoOff = Measurement(limits['Notify'], sense.oYesNoOff)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # OutputFuseCheck: Remove output fuse, Mains on, measure, restore fuse.
        msr1 = MeasureSubStep((m.ui_NotifyStart, ))
        acs1 = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr2 = MeasureSubStep((m.dmm_12Voff, m.ui_YesNoRed), timeout=5)
        acs2 = AcSubStep(
            acs=d.acsource, voltage=0.0, output=True, delay=0.5)
        msr3 = MeasureSubStep((m.ui_NotifyFuse, ))
        self.fuse_check = Step((msr1, acs1, msr2, acs2, msr3))
        # PowerUp: Apply 240Vac, measure.
        acs = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = MeasureSubStep(
            (m.dmm_12V_1, m.dmm_12V_2, m.dmm_12V_3,
             m.ui_YesNoGreen), timeout=5)
        self.pwr_up = Step((acs, msr))
        # FullLoad: Full load, measure.
        ld = LoadSubStep(((d.dcl, 25.0),), output=True)
        msr = MeasureSubStep((m.dmm_12Vfl, ), timeout=5)
        self.full_load = Step((ld, msr))
        # PowerOff: Switch mains off, measure.
        acs = AcSubStep(acs=d.acsource, voltage=0.0, delay=0.5)
        msr = MeasureSubStep(
            (m.ui_NotifyMains, m.dmm_12Voff, m.ui_YesNoOff), timeout=5)
        self.pwr_off = Step((acs, msr))
