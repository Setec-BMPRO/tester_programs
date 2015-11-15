#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Final Test Program."""

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
        self.dcl = dcload.DCLoad(devices['DCL5'])
        self.rla_load = relay.Relay(devices['RLA2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Load
        self.dcl.output(0.0, False)
        # Switch off Relay
        self.rla_load.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oVout = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=translate('c15a15_final', 'IsPowerLedGreen?'),
            caption=translate('c15a15_final', 'capPowerLed'))
        self.oYesNoYellowOff = sensor.YesNo(
            message=translate('c15a15_final', 'IsYellowLedOff?'),
            caption=translate('c15a15_final', 'capOutputLed'))
        self.oNotifyYellow = sensor.Notify(
            message=translate('c15a15_final', 'WatchYellowLed'),
            caption=translate('c15a15_final', 'capOutputLed'))
        self.oYesNoYellowOn = sensor.YesNo(
            message=translate('c15a15_final', 'IsYellowLedOn?'),
            caption=translate('c15a15_final', 'capOutputLed'))
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=0.0, stop=0.5, step=0.05, delay=0.2)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_Voutfl = Measurement(limits['Voutfl'], sense.oVout)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoYellowOff = Measurement(
            limits['Notify'], sense.oYesNoYellowOff)
        self.ui_NotifyYellow = Measurement(
            limits['Notify'], sense.oNotifyYellow)
        self.ui_YesNoYellowOn = Measurement(
            limits['Notify'], sense.oYesNoYellowOn)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # PowerUp: Apply 240Vac, measure.
        acs = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        ld = LoadSubStep(((d.dcl, 0.0), ), output=True)
        msr = MeasureSubStep(
            (m.dmm_Vout, m.ui_YesNoGreen, m.ui_YesNoYellowOff,
             m.ui_NotifyYellow, ), timeout=5)
        self.pwr_up = Step((acs, ld, msr))
        # OCP:
        rly1 = RelaySubStep(((d.rla_load, True), ))
        msr1 = MeasureSubStep((m.ramp_OCP, ), timeout=5)
        rly2 = RelaySubStep(((d.rla_load, False), ))
        msr2 = MeasureSubStep((m.ui_YesNoYellowOn, m.dmm_Vout,), timeout=5)
        self.ocp = Step((rly1, msr1, rly2, msr2))
        # FullLoad: full load, measure, recover.
        ld1 = LoadSubStep(((d.dcl, 1.31), ), output=True)
        msr1 = MeasureSubStep((m.dmm_Voutfl, ), timeout=5)
        ld2 = LoadSubStep(((d.dcl, 0.0),))
        msr2 = MeasureSubStep((m.dmm_Vout, ), timeout=5)
        self.full_load = Step((ld1, msr1, ld2, msr2))
        # PowerOff: Input AC off, discharge.
        ld = LoadSubStep(((d.dcl, 1.0),))
        acs = AcSubStep(acs=d.acsource, voltage=0.0, delay=2)
        self.pwr_off = Step((ld, acs))
