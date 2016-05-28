#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C45A-15 Final Test Program."""

import sensor
import tester
from tester.devlogical import *
from tester.measure import *

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.rla_Bus = relay.Relay(devices['RLA1'])
        self.dcl = dcload.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(0.0, False)
        self.rla_Bus.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oVout = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=translate('c45a15_final', 'IsPowerLedGreen?'),
            caption=translate('c45a15_final', 'capPowerLed'))
        self.oYesNoYellow = sensor.YesNo(
            message=translate('c45a15_final', 'WaitYellowLedOn?'),
            caption=translate('c45a15_final', 'capOutputLed'))
        self.oYesNoRed = sensor.YesNo(
            message=translate('c45a15_final', 'WaitRedLedFlash?'),
            caption=translate('c45a15_final', 'capOutputLed'))
        self.oNotifyOff = sensor.Notify(
            message=translate('c45a15_final', 'WaitAllLedsOff'),
            caption=translate('c45a15_final', 'capAllOff'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_Vstart = Measurement(limits['Vstart'], sense.oVout)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_Vshdn = Measurement(limits['Vshdn'], sense.oVout)
        self.dmm_Voff = Measurement(limits['Voff'], sense.oVout)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoYellow = Measurement(limits['Notify'], sense.oYesNoYellow)
        self.ui_YesNoRed = Measurement(limits['Notify'], sense.oYesNoRed)
        self.ui_NotifyOff = Measurement(limits['Notify'], sense.oNotifyOff)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # PowerUp: Apply 240Vac, measure.
        acs = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = MeasureSubStep((m.dmm_Vstart, m.ui_YesNoGreen), timeout=5)
        self.pwr_up = Step((acs, msr))

        # ConnectCMR: Apply 240Vac, measure.
        rly = RelaySubStep(((d.rla_Bus, True), ))
        msr = MeasureSubStep(
            (m.ui_YesNoYellow, m.dmm_Vout, m.ui_YesNoRed), timeout=8)
        self.connect_cmr = Step((rly, msr))

        # Load: startup load, full load, shutdown load.
        ld1 = LoadSubStep(((d.dcl, 0.3), ), output=True)
        msr1 = MeasureSubStep((m.dmm_Vout, ), timeout=5)
        ld2 = LoadSubStep(((d.dcl, 2.8),), delay=2)
        msr2 = MeasureSubStep((m.dmm_Vout, ), timeout=5)
        ld3 = LoadSubStep(((d.dcl, 3.5), ))
        msr3 = MeasureSubStep((m.dmm_Vshdn, ), timeout=5)
        self.load = Step((ld1, msr1, ld2, msr2, ld3, msr3))

        # Restart: Switch mains off, measure.
        acs1 = AcSubStep(acs=d.acsource, voltage=0.0)
        ld1 = LoadSubStep(((d.dcl, 2.8),), delay=5)
        ld2 = LoadSubStep(((d.dcl, 0.0),), delay=10)
        acs2 = AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr = MeasureSubStep((m.dmm_Vstart, ), timeout=5)
        self.restart = Step((acs1, ld1, ld2, acs2, msr))

        # PowerOff: Discharge, switch off, measure.
        ld = LoadSubStep(((d.dcl, 2.8), ))
        acs = AcSubStep(acs=d.acsource, voltage=0.0)
        msr = MeasureSubStep((m.dmm_Voff, m.ui_NotifyOff), timeout=5)
        self.pwr_off = Step((ld, acs, msr))
