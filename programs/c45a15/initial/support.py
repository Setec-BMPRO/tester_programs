#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C45A-15 Initial Test Program."""

import os
import inspect
import time
from pydispatch import dispatcher

import tester
import sensor
import share
from . import limit


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.acsource = tester.ACSource(devices['ACS'])
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_Vout = tester.DCSource(devices['DCS1'])
        self.dcs_Vbias = tester.DCSource(devices['DCS2'])
        self.dcs_VsecBias = tester.DCSource(devices['DCS3'])
        self.dcl = tester.DCLoad(devices['DCL1'])
        self.rla_Load = tester.Relay(devices['RLA1'])
        self.rla_CMR = tester.Relay(devices['RLA2'])
        self.rla_Prog = tester.Relay(devices['RLA4'])
        self.discharge = tester.Discharge(devices['DIS'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_pic = share.ProgramPIC(
            limit.PIC_HEX, folder, '16F684', self.rla_Prog)


    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(5.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_Vout, self.dcs_Vbias, self.dcs_VsecBias):
            dcs.output(0.0, False)
        self.dcl.output(0.0, False)
        for rla in (self.rla_Load, self.rla_CMR, self.rla_Prog):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oMirReg = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)
        self.oLock = sensor.Res(dmm, high=14, low=6, rng=10000, res=1)
        self.oVac = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self.oVbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.oVcc = sensor.Vdc(dmm, high=6, low=2, rng=100, res=0.01)
        self.oVsecBiasIn = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self.oVref = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.01)
        self.oVoutPre = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.01)
        self.oVout = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.01)
        self.oVsense = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.oGreen = sensor.Vdc(dmm, high=10, low=3, rng=10, res=0.01)
        self.oYellow = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.01)
        self.oRed = sensor.Vdc(dmm, high=12, low=3, rng=10, res=0.01)
        self.oOVP = sensor.Ramp(
            stimulus=logical_devices.dcs_Vout, sensor=self.oVcc,
            detect_limit=(limits['inOVP'], ),
            start=18.0, stop=22.0, step=0.1, delay=0.05)
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=1.0, stop=3.2, step=0.03, delay=0.1)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirReg.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.loadReg = Measurement(limits['Reg'], sense.oMirReg)
        self.dmm_Lock = Measurement(limits['FixtureLock'], sense.oLock)
        self.dmm_VacStart = Measurement(limits['VacStart'], sense.oVac)
        self.dmm_Vac = Measurement(limits['Vac'], sense.oVac)
        self.dmm_Vbus = Measurement(limits['Vbus'], sense.oVbus)
        self.dmm_Vcc = Measurement(limits['Vcc'], sense.oVcc)
        self.dmm_VsecBiasIn = Measurement(
            limits['SecBiasIn'], sense.oVsecBiasIn)
        self.dmm_Vref = Measurement(limits['Vref'], sense.oVref)
        self.dmm_VrefOff = Measurement(limits['VrefOff'], sense.oVref)
        self.dmm_VoutPreExt = Measurement(limits['VoutPreExt'], sense.oVoutPre)
        self.dmm_VoutExt = Measurement(limits['VoutExt'], sense.oVout)
        self.dmm_VoutPre = Measurement(limits['VoutPre'], sense.oVoutPre)
        self.dmm_VoutLow = Measurement(limits['VoutLow'], sense.oVout)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_VsenseLow = Measurement(limits['VsenseLow'], sense.oVsense)
        self.dmm_VsenseOn = Measurement(limits['VsenseOn'], sense.oVsense)
        self.dmm_VsenseOff = Measurement(limits['VsenseOff'], sense.oVsense)
        self.dmm_GreenOn = Measurement(limits['GreenOn'], sense.oGreen)
        self.dmm_GreenOff = Measurement(limits['LedOff'], sense.oGreen)
        self.dmm_YellowOn = Measurement(limits['YellowOn'], sense.oYellow)
        self.dmm_YellowOff = Measurement(limits['LedOff'], sense.oYellow)
        self.dmm_RedOn = Measurement(limits['RedOn'], sense.oRed)
        self.dmm_RedOff = Measurement(limits['LedOff'], sense.oRed)
        self.ramp_OVP = Measurement(limits['OVP'], sense.oOVP)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # SecCheck: Apply external voltages, measure.
        dcs1 = tester.DcSubStep(
            setting=((d.dcs_Vout, 12.0),), output=True)
        msr1 = tester.MeasureSubStep(
            (m.dmm_VoutPreExt, m.dmm_VsenseOff, m.dmm_VoutExt, ), timeout=5)
        dcs2 = tester.DcSubStep(setting=(
            (d.dcs_VsecBias, 12.0), ), output=True, delay=1)
        msr2 = tester.MeasureSubStep(
            (m.dmm_Vref, m.dmm_VsenseOn, m.dmm_VoutExt,), timeout=5)
        self.sec_chk = tester.SubStep((dcs1, msr1, dcs2, msr2))
        # OVP: Reset the PIC device and measure OVP.
        dcs1 = tester.DcSubStep(setting=((d.dcs_VsecBias, 0.0), ), delay=0.5)
        msr1 = tester.MeasureSubStep((m.dmm_VrefOff, ), timeout=5)
        dcs2 = tester.DcSubStep(setting=((d.dcs_VsecBias, 12.0), ))
        msr2 = tester.MeasureSubStep((m.dmm_GreenOn, ), timeout=5)
        dcs3 = tester.DcSubStep(setting=((d.dcs_Vbias, 12.0), ))
        msr3 = tester.MeasureSubStep((m.dmm_Vcc, m.ramp_OVP), timeout=5)
        dcs4 = tester.DcSubStep(
            setting=((d.dcs_Vout, 0.0), (d.dcs_Vbias, 0.0),
                     (d.dcs_VsecBias, 0.0)), output=False, delay=1)
        self.OVP = tester.SubStep((dcs1, msr1, dcs2, msr2, dcs3, msr3, dcs4))
        # PowerUp: Apply 95Vac, 240Vac, measure.
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=95.0, output=True, delay=0.5)
        msr1 = tester.MeasureSubStep(
            (m.dmm_VacStart, m.dmm_Vcc, m.dmm_Vref, m.dmm_GreenOn,
             m.dmm_YellowOff, m.dmm_RedOff, m.dmm_VoutLow, m.dmm_VsenseLow, ),
            timeout=5)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr2 = tester.MeasureSubStep((m.dmm_Vac, m.dmm_VoutLow, ), timeout=5)
        rly1 = tester.RelaySubStep(((d.rla_CMR, True), ))
        msr3 = tester.MeasureSubStep(
            (m.dmm_YellowOn, m.dmm_Vout, m.dmm_RedOn, ), timeout=12)
        self.pwr_up = tester.SubStep((acs1, msr1, acs2, msr2, rly1, msr3))
