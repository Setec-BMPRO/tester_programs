#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STxx-III Final Test Program."""

import time
import sensor
import tester
from tester.devlogical import *
from tester.measure import *

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.devlogical.dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcl_Load = dcload.DCLoad(devices['DCL1'])
        self.dcl_Batt = dcload.DCLoad(devices['DCL5'])
        self.rla_BattSw = relay.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_Load.output(5.0, True)
        time.sleep(0.5)
        for dcl in (self.dcl_Load, self.dcl_Batt):
            dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oLoad = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oFuse1 = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oFuse2 = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.001)
        self.oFuse3 = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self.oFuse4 = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self.oFuse5 = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.001)
        self.oFuse6 = sensor.Vdc(dmm, high=6, low=1, rng=100, res=0.001)
        self.oFuse7 = sensor.Vdc(dmm, high=7, low=1, rng=100, res=0.001)
        self.oFuse8 = sensor.Vdc(dmm, high=8, low=1, rng=100, res=0.001)
        self.oBatt = sensor.Vdc(dmm, high=9, low=2, rng=100, res=0.001)
        self.oAlarm = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        self.oBarcode = sensor.DataEntry(
            message=translate('st3_final', 'ScanBarcode'),
            caption=translate('st3_final', 'capBarcode'))
        self.oYesNoOrGr = sensor.YesNo(
            message=translate('st3_final', 'AreOrangeGreen?'),
            caption=translate('st3_final', 'capOrangeGreen'))
        self.oYesNoRedOn = sensor.YesNo(
            message=translate('st3_final', 'RemoveBattFuseIsRedBlink?'),
            caption=translate('st3_final', 'capRed'))
        self.oYesNoRedOff = sensor.YesNo(
            message=translate('st3_final', 'ReplaceBattFuseIsRedOff?'),
            caption=translate('st3_final', 'capRed'))
        ocp_start, ocp_stop = limits['LoadOCPramp'].limit
        self.oLoadOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Load, sensor=self.oLoad,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.2, delay=0.1, reset=False)
        ocp_start, ocp_stop = limits['BattOCPramp'].limit
        self.oBattOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Batt, sensor=self.oBatt,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.2, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.barcode = Measurement(limits['FuseLabel'], sense.oBarcode)
        self.dmm_Load = Measurement(limits['Vout'], sense.oLoad)
        self.dmm_Boost = Measurement(limits['Vboost'], sense.oLoad)
        self.dmm_Batt = Measurement(limits['Vbat'], sense.oBatt)
        self.dmm_Fuse1 = Measurement(limits['FuseIn'], sense.oFuse1)
        self.dmm_Fuse2 = Measurement(limits['FuseIn'], sense.oFuse2)
        self.dmm_Fuse3 = Measurement(limits['FuseIn'], sense.oFuse3)
        self.dmm_Fuse4 = Measurement(limits['FuseIn'], sense.oFuse4)
        self.dmm_Fuse5 = Measurement(limits['FuseIn'], sense.oFuse5)
        self.dmm_Fuse6 = Measurement(limits['FuseIn'], sense.oFuse6)
        self.dmm_Fuse7 = Measurement(limits['FuseIn'], sense.oFuse7)
        self.dmm_Fuse8 = Measurement(limits['FuseIn'], sense.oFuse8)
        self.ui_YesNoOrGr = Measurement(limits['Notify'], sense.oYesNoOrGr)
        self.ui_YesNoRedOn = Measurement(limits['Notify'], sense.oYesNoRedOn)
        self.ui_YesNoRedOff = Measurement(limits['Notify'], sense.oYesNoRedOff)
        self.dmm_BattFuseOut = Measurement(limits['FuseOut'], sense.oBatt)
        self.dmm_BattFuseIn = Measurement(limits['FuseIn'], sense.oBatt)
        self.ramp_LoadOCP = Measurement(limits['LoadOCP'], sense.oLoadOCP)
        self.dmm_Overload = Measurement(limits['Voff'], sense.oLoad)
        self.ramp_BattOCP = Measurement(limits['BattOCP'], sense.oBattOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: 240Vac, measure.
        acs1 = AcSubStep(acs=d.acsource, voltage=240.0, output=True)
        msr1 = MeasureSubStep(
            (m.dmm_Boost, m.dmm_Fuse1, m.dmm_Fuse2, m.dmm_Fuse3, m.dmm_Fuse4,
             m.dmm_Fuse5, m.dmm_Fuse6, m.dmm_Fuse7, m.dmm_Fuse8,
             m.dmm_Batt, m.ui_YesNoOrGr, ), timeout=10)
        self.power_up = Step((acs1, msr1, ))
        # Battery: Load, SwitchOff, measure, SwitchOn,
        #           PullFuse, measure, ReplaceFuse, measure, unload
        dcl1 = LoadSubStep(
            ((d.dcl_Batt, 2.0), (d.dcl_Load, 0.0), ), output=True)
        rla1 = RelaySubStep(((d.rla_BattSw, True), ))
        msr1 = MeasureSubStep((m.dmm_BattFuseOut, ), timeout=5)
        dcl2 = LoadSubStep(((d.dcl_Batt, 0.0), ))
        rla2 = RelaySubStep(((d.rla_BattSw, False), ), delay=0.5)
        msr2 = MeasureSubStep(
            (m.dmm_BattFuseIn, m.ui_YesNoRedOn, m.ui_YesNoRedOff, ), timeout=5)
        self.battery = Step((dcl1, rla1, msr1, dcl2, rla2, msr2, ))
