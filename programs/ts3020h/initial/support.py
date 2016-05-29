#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TS3020H Initial Test Program."""

import time
from pydispatch import dispatcher

import sensor
import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.acsource = tester.ACSource(devices['ACS'])
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_Vout = tester.DCSource(devices['DCS3'])
        self.dcs_SecCtl2 = tester.DCSource(devices['DCS2'])
        self.dcl = tester.DCLoad(devices['DCL1'])
        self.rla_Fuse = tester.Relay(devices['RLA4'])
        self.rla_Fan = tester.Relay(devices['RLA6'])
        self.discharge = tester.Discharge(devices['DIS'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(5.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_Vout, self.dcs_SecCtl2):
            dcs.output(0.0, False)
        self.dcl.output(0.0, False)
        for rla in (self.rla_Fuse, self.rla_Fan):
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
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.oLock = sensor.Res(dmm, high=17, low=5, rng=10000, res=1)
        self.oFanConn = sensor.Res(dmm, high=6, low=6, rng=1000, res=1)
        self.oInrush = sensor.Res(dmm, high=1, low=2, rng=1000, res=0.1)
        self.oVout = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self.oSecCtl = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.01)
        self.oSecCtl2 = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.01)
        self.oGreenLed = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.01)
        self.oRedLed = sensor.Vdc(dmm, high=10, low=3, rng=10, res=0.01)
        self.oFan12V = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.1)
        self.oSecShdn = sensor.Vdc(dmm, high=16, low=3, rng=100, res=0.01)
        self.oVbus = sensor.Vdc(dmm, high=3, low=1, rng=1000, res=0.1)
        self.oVbias = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.1)
        self.oAcDetect = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        self.oVac = sensor.Vac(dmm, high=2, low=4, rng=1000, res=0.1)
        self.oPWMShdn = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.01)
        self.oVacOVShdn = sensor.Vdc(dmm, high=15, low=1, rng=100, res=0.01)
        vout_low, vout_high = limits['VoutSet'].limit
        self.oAdjVout = sensor.AdjustAnalog(
            sensor=self.oVout,
            low=vout_low, high=vout_high,
            message=tester.translate('ts3020h_initial', 'AdjR130'),
            caption=tester.translate('ts3020h_initial', 'capAdjOutput'))
        self.oOVP = sensor.Ramp(
            stimulus=logical_devices.dcs_Vout, sensor=self.oSecShdn,
            detect_limit=(limits['inVP'], ),
            start=14.5, stop=17.0, step=0.05, delay=0.1)
        self.oUVP = sensor.Ramp(
            stimulus=logical_devices.dcs_Vout, sensor=self.oSecShdn,
            detect_limit=(limits['inVP'], ),
            start=11.5, stop=8.0, step=-0.1, delay=0.3)

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
        self.dmm_reg = Measurement(limits['Reg'], sense.oMirReg)
        self.dmm_Lock = Measurement(limits['FixtureLock'], sense.oLock)
        self.dmm_FanConn = Measurement(limits['FanConn'], sense.oFanConn)
        self.dmm_InrushOff = Measurement(limits['InrushOff'], sense.oInrush)
        self.dmm_InrushOn = Measurement(limits['InrushOn'], sense.oInrush)
        self.dmm_VoutExt = Measurement(limits['VoutExt'], sense.oVout)
        self.dmm_VoutPre = Measurement(limits['VoutPre'], sense.oVout)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_VoutSet = Measurement(limits['VoutSet'], sense.oVout)
        self.dmm_VoutOff = Measurement(limits['VoutOff'], sense.oVout)
        self.dmm_SecCtlExt = Measurement(limits['SecCtlExt'], sense.oSecCtl)
        self.dmm_SecCtl2Ext = Measurement(limits['SecCtl2Ext'], sense.oSecCtl2)
        self.dmm_SecCtl = Measurement(limits['SecCtl'], sense.oSecCtl)
        self.dmm_SecCtl2 = Measurement(limits['SecCtl2'], sense.oSecCtl2)
        self.dmm_GreenOn = Measurement(limits['LedOn'], sense.oGreenLed)
        self.dmm_GreenOff = Measurement(limits['LedOff'], sense.oGreenLed)
        self.dmm_RedOn = Measurement(limits['LedOn'], sense.oRedLed)
        self.dmm_RedOff = Measurement(limits['LedOff'], sense.oRedLed)
        self.dmm_FanOff = Measurement(limits['FanOff'], sense.oFan12V)
        self.dmm_FanOn = Measurement(limits['FanOn'], sense.oFan12V)
        self.dmm_VbusExt = Measurement(limits['VbusExt'], sense.oVbus)
        self.dmm_VbusOff = Measurement(limits['VbusOff'], sense.oVbus)
        self.dmm_Vbus = Measurement(limits['Vbus'], sense.oVbus)
        self.dmm_Vbias = Measurement(limits['Vbias'], sense.oVbias)
        self.dmm_AcDetOff = Measurement(limits['AcDetOff'], sense.oAcDetect)
        self.dmm_AcDetOn = Measurement(limits['AcDetOn'], sense.oAcDetect)
        self.dmm_VacMin = Measurement(limits['VacMin'], sense.oVac)
        self.dmm_Vac = Measurement(limits['Vac'], sense.oVac)
        self.dmm_SecShdnOff = Measurement(limits['SecShdnOff'], sense.oSecShdn)
        self.dmm_pwmShdnOn = Measurement(limits['PwmShdnOn'], sense.oPWMShdn)
        self.dmm_pwmShdnOff = Measurement(limits['PwmShdnOff'], sense.oPWMShdn)
        self.dmm_vacShdnOn = Measurement(limits['VacShdnOn'], sense.oVacOVShdn)
        self.dmm_vacShdnOff = Measurement(
            limits['VacShdnOff'], sense.oVacOVShdn)
        self.ramp_OVP = Measurement(limits['OVP'], sense.oOVP)
        self.ramp_UVP = Measurement(limits['UVP'], sense.oUVP)
        self.ui_AdjVout = Measurement(limits['Notify'], sense.oAdjVout)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # FuseCheck: Apply ext Vout and SecCtl2, measure.
        dcs1 = tester.DcSubStep(
            setting=((d.dcs_Vout, 13.8), (d.dcs_SecCtl2, 13.8), ), output=True)
        msr1 = tester.MeasureSubStep(
            (m.dmm_VoutExt, m.dmm_SecCtl2Ext, m.dmm_SecCtlExt, ), timeout=5)
        rly1 = tester.RelaySubStep(((d.rla_Fuse, True), ))
        msr2 = tester.MeasureSubStep(
            (m.dmm_GreenOn, m.dmm_RedOff), timeout=5)
        rly2 = tester.RelaySubStep(((d.rla_Fuse, False), ))
        msr3 = tester.MeasureSubStep(
            (m.dmm_GreenOff, m.dmm_RedOn), timeout=5)
        self.fuse_check = tester.SubStep(
            (dcs1, msr1, rly1, msr2, rly2, msr3))
        # FanCheck: Activate fan, measure.
        msr1 = tester.MeasureSubStep((m.dmm_FanOff, ), timeout=5)
        rly1 = tester.RelaySubStep(((d.rla_Fan, True), ))
        msr2 = tester.MeasureSubStep(
            (m.dmm_FanOn, m.dmm_SecShdnOff), timeout=10)
        rly2 = tester.RelaySubStep(((d.rla_Fan, False), ))
        self.fan_check = tester.SubStep((msr1, rly1, msr2, rly2))
        # VoltageProtect: Measure OVP and UVP.
        msr1 = tester.MeasureSubStep((m.ramp_OVP, ), timeout=5)
        ld1 = tester.LoadSubStep(((d.dcl, 0.5), ), output=True)
        msr2 = tester.MeasureSubStep((m.ramp_UVP, ), timeout=5)
        ld2 = tester.LoadSubStep(((d.dcl, 0.0),))
        self.OV_UV = tester.SubStep((msr1, ld1, msr2, ld2))
        # PowerUp: Turn on at low voltage measure
        dcs1 = tester.DcSubStep(
            setting=((d.dcs_Vout, 0.0), (d.dcs_SecCtl2, 0.0), ), output=False)
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=100.0, output=True, delay=1.0)
        msr1 = tester.MeasureSubStep(
            (m.dmm_VacMin, m.dmm_AcDetOn, m.dmm_InrushOn, m.dmm_Vbus,
             m.dmm_VoutPre, m.dmm_SecCtl, m.dmm_SecCtl2, ), timeout=5)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=0.0)
        self.pwr_up = tester.SubStep((dcs1, acs1, msr1, acs2))
        # MainsCheck: Turn on, min load, measure.
        ld1 = tester.LoadSubStep(((d.dcl, 0.5), ), output=True)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=75.0, delay=2.0)
        msr1 = tester.MeasureSubStep((m.dmm_AcDetOff, ), timeout=7)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=94.0,  delay=0.5)
        msr2 = tester.MeasureSubStep((m.dmm_AcDetOn, ), timeout=7)
        acs3 = tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        msr3 = tester.MeasureSubStep(
            (m.dmm_Vac, m.dmm_AcDetOn, m.dmm_Vbias, m.dmm_SecCtl,
             m.dmm_VoutPre, ), timeout=5)
        self.mains_chk = tester.SubStep(
            (ld1, acs1, msr1, acs2, msr2, acs3, msr3))
        # Load: Load, measure, overload, shutdown.
        ld1 = tester.LoadSubStep(((d.dcl, 16.0), ))
        msr1 = tester.MeasureSubStep(
            (m.dmm_Vbus, m.dmm_Vbias, m.dmm_SecCtl, m.dmm_SecCtl2,
             m.dmm_Vout, ), timeout=5)
        ld2 = tester.LoadSubStep(((d.dcl, 30.05),), delay=1)
        msr2 = tester.MeasureSubStep((m.dmm_VoutOff, ), timeout=10)
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=0.0)
        ld3 = tester.LoadSubStep(((d.dcl, 0.0), ))
        self.load = tester.SubStep((ld1, msr1))
        self.shutdown = tester.SubStep((ld2, msr2, acs1, ld3))
        # InputOV: Apply input overvoltage, shutdown.
        ld1 = tester.LoadSubStep(((d.dcl, 0.5), ))
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr1 = tester.MeasureSubStep(
            (m.dmm_pwmShdnOn, m.dmm_vacShdnOn, ), timeout=8)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=300.0, delay=0.5)
        msr2 = tester.MeasureSubStep(
            (m.dmm_pwmShdnOff, m.dmm_vacShdnOn, ), timeout=8)
        acs4 = tester.AcSubStep(acs=d.acsource, voltage=0.0)
        self.inp_ov = tester.SubStep((ld1, acs1, msr1, acs2, msr2, acs4))
