#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Final Test Program."""

import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl = tester.DCLoad(devices['DCL5'])
        self.rla_load = tester.Relay(devices['RLA2'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(0.0, False)
        self.rla_load.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oVout = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('c15a15_final', 'IsPowerLedGreen?'),
            caption=tester.translate('c15a15_final', 'capPowerLed'))
        self.oYesNoYellowOff = sensor.YesNo(
            message=tester.translate('c15a15_final', 'IsYellowLedOff?'),
            caption=tester.translate('c15a15_final', 'capOutputLed'))
        self.oNotifyYellow = sensor.Notify(
            message=tester.translate('c15a15_final', 'WatchYellowLed'),
            caption=tester.translate('c15a15_final', 'capOutputLed'))
        self.oYesNoYellowOn = sensor.YesNo(
            message=tester.translate('c15a15_final', 'IsYellowLedOn?'),
            caption=tester.translate('c15a15_final', 'capOutputLed'))
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=0.0, stop=0.5, step=0.05, delay=0.2)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
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
        acs = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        ld = tester.LoadSubStep(((d.dcl, 0.0), ), output=True)
        msr = tester.MeasureSubStep(
            (m.dmm_Vout, m.ui_YesNoGreen, m.ui_YesNoYellowOff,
             m.ui_NotifyYellow, ), timeout=5)
        self.pwr_up = tester.SubStep((acs, ld, msr))
        # OCP:
        rly1 = tester.RelaySubStep(((d.rla_load, True), ))
        msr1 = tester.MeasureSubStep((m.ramp_OCP, ), timeout=5)
        rly2 = tester.RelaySubStep(((d.rla_load, False), ))
        msr2 = tester.MeasureSubStep((m.ui_YesNoYellowOn, m.dmm_Vout,), timeout=5)
        self.ocp = tester.SubStep((rly1, msr1, rly2, msr2))
        # FullLoad: full load, measure, recover.
        ld1 = tester.LoadSubStep(((d.dcl, 1.31), ), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_Voutfl, ), timeout=5)
        ld2 = tester.LoadSubStep(((d.dcl, 0.0),))
        msr2 = tester.MeasureSubStep((m.dmm_Vout, ), timeout=5)
        self.full_load = tester.SubStep((ld1, msr1, ld2, msr2))
        # PowerOff: Input AC off, discharge.
        ld = tester.LoadSubStep(((d.dcl, 1.0),))
        acs = tester.AcSubStep(acs=d.acsource, voltage=0.0, delay=2)
        self.pwr_off = tester.SubStep((ld, acs))
