#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TS3020H Initial Test Program."""

import time
from pydispatch import dispatcher
import tester

LIMITS = tester.testlimit.limitset((
    ('FanConn', 0, 100, 200, None, None),
    ('InrushOff', 0, 120, 180, None, None),
    ('InrushOn', 0, 10, None, None, None),
    ('SecCtlExt', 1, 12.8, 14.0, None, None),
    ('SecCtl2Ext', 1, 13.6, 14.0, None, None),
    ('SecCtl', 1, 9.6, 15.0, None, None),
    ('SecCtl2', 1, 7.0, 15.0, None, None),
    ('LedOn', 1, 1.5, 2.2, None, None),
    ('LedOff', 1, -0.1, 0.1, None, None),
    ('FanOff', 1, 13.4, 14.0, None, None),
    ('FanOn', 1, -0.5, 1.0, None, None),
    ('inVP', 1, 12.5, None, None, None),
    ('OVP', 1, 14.95, 16.45, None, None),
    ('UVP', 1, 9.96, 10.96, None, None),
    ('VbusExt', 1, 118.0, 122.0, None, None),
    ('VbusOff', 1, 70.0, None, None, None),
    ('Vbus', 1, 380.0, 410.0, None, None),
    ('Vbias', 1, 11.2, 12.8, None, None),
    ('AcDetOff', 1, -0.1, 6.0, None, None),
    ('AcDetOn', 1, 8.0, 14.0, None, None),
    ('VacMin', 1, 95.0, 105.0, None, None),
    ('Vac', 1, 237.0, 242.0, None, None),
    ('VoutExt', 1, 13.6, 14.0, None, None),
    ('VoutPre', 1, 12.6, 15.0, None, None),
    ('VoutSet', 1, 13.775, 13.825, None, None),
    ('Vout', 1, 13.5, 13.825, None, None),
    ('VoutOff', 1, 5.0, None, None, None),
    ('Reg', 1, 2.0, None, None, None),
    ('SecShdnOff', 1, 12.5, 13.5, None, None),
    ('PwmShdnOn', 1, 9.0, 15.0, None, None),
    ('PwmShdnOff', 1, 1.0, None, None, None),
    ('VacShdnOn', 1, 9.0, 15.0, None, None),
    ('VacShdnOff', 1, 1.0, None, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """TS3020H Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('FuseCheck', self._step_fuse_check),
            tester.TestStep('FanCheck', self._step_fan_check),
            tester.TestStep('OutputOV_UV', self._step_ov_uv),
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('MainsCheck', self._step_mains_check),
            tester.TestStep('AdjOutput', self._step_adj_output),
            tester.TestStep('Load', self._step_load),
            tester.TestStep('InputOV', self._step_input_ov),
            )
        self._limits = LIMITS
        global m, d, s, t
        d = LogicalDevices(self.physical_devices)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)
        t = SubTests(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(
            ((s.oLock, 10.0), (s.oFanConn, 150.0), (s.oInrush, 160.0), ))
        tester.MeasureGroup(
            (m.dmm_Lock, m.dmm_FanConn, m.dmm_InrushOff), timeout=5)

    def _step_fuse_check(self):
        """Check for output fuse in/out.

        Apply external Vout, SecCtl2 and measure led voltages.

        """
        self.fifo_push(
            ((s.oVout, 13.8), (s.oSecCtl, 13.5), (s.oSecCtl2, 13.8),
             (s.oGreenLed, (2.0, 0.0)), (s.oRedLed, (0.0, 2.0)), ))
        t.fuse_check.run()

    def _step_fan_check(self):
        """Check the operation of the fan.

        Apply external Vout, SecCtl2. Connect 56R to SecCtl to
        activate fan. Check for fan on/off.

        """
        self.fifo_push(
            ((s.oFan12V, (13.8, 0.5)), (s.oSecShdn, 13.0)))
        t.fan_check.run()

    def _step_ov_uv(self):
        """Apply external Vout and measure output OVP and UVP."""
        self.fifo_push(
            ((s.oSecShdn, ((13.0, ) * 14 + (12.4, )) * 2, ), ))
        t.OV_UV.run()

    def _step_power_up(self):
        """Apply low input AC and measure primary voltages."""
        self.fifo_push(
            ((s.oVac, 100.0), (s.oAcDetect, 11.0), (s.oInrush, 5.0),
             (s.oVbus, (400.0, 30.0)), (s.oVout, 13.8), (s.oSecCtl, 13.8),
             (s.oSecCtl2, 13.8), ))
        t.pwr_up.run()
        d.discharge.pulse(2.0)
        m.dmm_VbusOff.measure(timeout=10)

    def _step_mains_check(self):
        """Apply input AC with min load and measure voltages."""
        self.fifo_push(
            ((s.oAcDetect, 4.0), (s.oAcDetect, 11.0), (s.oVac, 240.0),
             (s.oAcDetect, 11.0), (s.oVbias, 12.0), (s.oSecCtl, 13.8),
             (s.oVout, 13.8), ))
        t.mains_chk.run()

    def _step_adj_output(self):
        """Adjust the output voltage.

        Set output voltage, apply load and measure voltages.

        """
#        self.fifo_push(((s.oAdjVout, True), ))
        self.fifo_push(
            ((s.oVout, (13.77, 13.78, 13.79, 13.8, 13.8)), ))
        m.ui_AdjVout.measure()
        m.dmm_VoutSet.measure(timeout=5)

    def _step_load(self):
        """Measure output voltage under load conditions.

           Load and measure output.
           Check output regulation.
           Check for shutdown with overload.

        """
        self.fifo_push(
            ((s.oVbus, 400.0), (s.oVbias, 12.0), (s.oSecCtl, 13.8),
             (s.oSecCtl2, 13.8), (s.oVout, (13.8, 13.8, 13.7, 0.0)),))
        t.load.run()
        # Measure load regulation
        d.dcl.output(0.0)
        noload = m.dmm_Vout.measure(timeout=5).reading1
        d.dcl.output(24.0)
        fullload = m.dmm_Vout.measure(timeout=5).reading1
        reg = ((noload - fullload) / noload) * 100
        s.oMirReg.store(reg)
        m.dmm_reg.measure()
        t.shutdown.run()

    def _step_input_ov(self):
        """Check for shutdown with input over voltage."""
        self.fifo_push(((s.oPWMShdn, (10.0, 0.5, 0.5)), ))
        t.inp_ov.run()


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
        sensor = tester.sensor
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
