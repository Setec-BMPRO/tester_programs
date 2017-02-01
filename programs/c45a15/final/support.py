#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C45A-15 Final Test Program."""

import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.rla_Bus = tester.Relay(devices['RLA1'])
        self.dcl = tester.DCLoad(devices['DCL1'])

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
        sensor = tester.sensor
        self.oVout = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('c45a15_final', 'IsPowerLedGreen?'),
            caption=tester.translate('c45a15_final', 'capPowerLed'))
        self.oYesNoYellow = sensor.YesNo(
            message=tester.translate('c45a15_final', 'WaitYellowLedOn?'),
            caption=tester.translate('c45a15_final', 'capOutputLed'))
        self.oYesNoRed = sensor.YesNo(
            message=tester.translate('c45a15_final', 'WaitRedLedFlash?'),
            caption=tester.translate('c45a15_final', 'capOutputLed'))
        self.oNotifyOff = sensor.Notify(
            message=tester.translate('c45a15_final', 'WaitAllLedsOff'),
            caption=tester.translate('c45a15_final', 'capAllOff'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
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
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr1 = tester.MeasureSubStep((m.dmm_Vstart, m.ui_YesNoGreen), timeout=5)
        self.pwr_up = tester.SubStep((acs1, msr1))

        # ConnectCMR: Apply 240Vac, measure.
        rly1 = tester.RelaySubStep(((d.rla_Bus, True), ))
        msr1 = tester.MeasureSubStep(
            (m.ui_YesNoYellow, m.dmm_Vout, m.ui_YesNoRed), timeout=8)
        self.connect_cmr = tester.SubStep((rly1, msr1))

        # Load: startup load, full load, shutdown load.
        ld1 = tester.LoadSubStep(((d.dcl, 0.3), ), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_Vout, ), timeout=5)
        ld2 = tester.LoadSubStep(((d.dcl, 2.8),), delay=2)
        msr2 = tester.MeasureSubStep((m.dmm_Vout, ), timeout=5)
        ld3 = tester.LoadSubStep(((d.dcl, 3.5), ))
        msr3 = tester.MeasureSubStep((m.dmm_Vshdn, ), timeout=5)
        self.load = tester.SubStep((ld1, msr1, ld2, msr2, ld3, msr3))

        # Restart: Switch mains off, measure.
        rly1 = tester.RelaySubStep(((d.rla_Bus, False), ))
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=0.0)
        ld1 = tester.LoadSubStep(((d.dcl, 2.8),), delay=1)
        ld2 = tester.LoadSubStep(((d.dcl, 0.0),), output=False, delay=1)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr1 = tester.MeasureSubStep((m.dmm_Vstart, ), timeout=5)
        self.restart = tester.SubStep((rly1, acs1, ld1, ld2, acs2, msr1))

        # PowerOff: Discharge, switch off, measure.
        ld1 = tester.LoadSubStep(((d.dcl, 2.8), ), output=True)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=0.0)
        msr1 = tester.MeasureSubStep((m.dmm_Voff, m.ui_NotifyOff), timeout=5)
        self.pwr_off = tester.SubStep((ld1, acs1, msr1))
