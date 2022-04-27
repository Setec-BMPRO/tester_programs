#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2014 SETEC Pty Ltd.
"""TS3020H Initial Test Program."""

import tester

import share


class Initial(share.TestSequence):

    """TS3020H Initial Test Program."""

    limitdata = (
        tester.LimitBetween('FanConn', 100, 200),
        tester.LimitBetween('InrushOff', 120, 180),
        tester.LimitLow('InrushOn', 10),
        tester.LimitBetween('SecCtlExt', 12.8, 14.0),
        tester.LimitBetween('SecCtl2Ext', 13.6, 14.0),
        tester.LimitBetween('SecCtl', 9.6, 15.0),
        tester.LimitBetween('SecCtl2', 7.0, 15.0),
        tester.LimitBetween('LedOn', 1.5, 2.2),
        tester.LimitBetween('LedOff', -0.1, 0.1),
        tester.LimitBetween('FanOff', 13.4, 14.0),
        tester.LimitBetween('FanOn', -0.5, 1.0),
        tester.LimitLow('inVP', 12.5),
        tester.LimitBetween('OVP', 14.95, 16.45),
        tester.LimitBetween('UVP', 9.96, 10.96),
        tester.LimitDelta('VbusExt', 120.0, 2.0),
        tester.LimitLow('VbusOff', 70.0),
        tester.LimitBetween('Vbus', 380.0, 410.0),
        tester.LimitBetween('Vbias', 11.2, 12.8),
        tester.LimitBetween('AcDetOff', -0.1, 6.0),
        tester.LimitBetween('AcDetOn', 8.0, 14.0),
        tester.LimitDelta('VacMin', 100.0, 5.0),
        tester.LimitDelta('Vac', 240.0, 5.0),
        tester.LimitBetween('VoutExt', 13.6, 14.0),
        tester.LimitBetween('VoutPre', 12.6, 15.0),
        tester.LimitBetween('VoutSet', 13.775, 13.825),
        tester.LimitBetween('Vout', 13.5, 13.825),
        tester.LimitLow('VoutOff', 5.0),
        tester.LimitLow('Reg', 2.0),
        tester.LimitBetween('SecShdnOff', 12.5, 13.5),
        tester.LimitBetween('PwmShdnOn', 9.0, 15.0),
        tester.LimitLow('PwmShdnOff', 1.0),
        tester.LimitBetween('VacShdnOn', 9.0, 15.0),
        tester.LimitLow('VacShdnOff', 1.0),
        tester.LimitLow('FixtureLock', 20),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
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

    @share.teststep
    def _step_fixture_lock(self, dev, mes):
        """Check that Fixture Lock is closed."""
        self.measure(('dmm_Lock', 'dmm_FanConn', 'dmm_InrushOff'), timeout=5)

    @share.teststep
    def _step_fuse_check(self, dev, mes):
        """Check for output fuse in/out.

        Apply external Vout, SecCtl2 and measure led voltages.

        """
        self.dcsource(
            (('dcs_Vout', 13.8), ('dcs_SecCtl2', 13.8), ), output=True)
        self.measure(
            ('dmm_VoutExt', 'dmm_SecCtl2Ext', 'dmm_SecCtlExt', ), timeout=5)
        dev['rla_Fuse'].set_on()
        self.measure(('dmm_GreenOn', 'dmm_RedOff'), timeout=5)
        dev['rla_Fuse'].set_off()
        self.measure(('dmm_GreenOff', 'dmm_RedOn'), timeout=5)

    @share.teststep
    def _step_fan_check(self, dev, mes):
        """Check the operation of the fan.

        Apply external Vout, SecCtl2. Connect 56R to SecCtl to
        activate fan. Check for fan on/off.

        """
        mes['dmm_FanOff'](timeout=5)
        dev['rla_Fan'].set_on()
        self.measure(('dmm_FanOn', 'dmm_SecShdnOff'), timeout=10)
        dev['rla_Fan'].set_off()

    @share.teststep
    def _step_ov_uv(self, dev, mes):
        """Apply external Vout and measure output OVP and UVP."""
        mes['ramp_OVP'](timeout=5)
        dev['dcl'].output(0.5, output=True)
        mes['ramp_UVP'](timeout=5)
        dev['dcl'].output(0.0)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply low input AC and measure primary voltages."""
        self.dcsource(
            (('dcs_Vout', 0.0), ('dcs_SecCtl2', 0.0), ), output=False)
        dev['acsource'].output(100.0, output=True, delay=1.0)
        self.measure(
            ('dmm_VacMin', 'dmm_AcDetOn', 'dmm_InrushOn', 'dmm_Vbus',
             'dmm_VoutPre', 'dmm_SecCtl', 'dmm_SecCtl2', ), timeout=5)
        dev['acsource'].output(0.0)
        dev['discharge'].pulse(1.0)
        mes['dmm_VbusOff'](timeout=10)

    @share.teststep
    def _step_mains_check(self, dev, mes):
        """Apply input AC with min load and measure voltages."""
        dev['dcl'].output(0.5, output=True)
        dev['acsource'].output(75.0, delay=2.0)
        mes['dmm_AcDetOff'](timeout=7)
        dev['acsource'].output(94.0, delay=0.5)
        mes['dmm_AcDetOn'](timeout=7)
        dev['acsource'].output(240.0, delay=0.5)
        self.measure(
            ('dmm_Vac', 'dmm_AcDetOn', 'dmm_Vbias', 'dmm_SecCtl',
             'dmm_VoutPre', ), timeout=5)

    @share.teststep
    def _step_adj_output(self, dev, mes):
        """Adjust the output voltage.

        Set output voltage, apply load and measure voltages.

        """
        mes['ui_AdjVout']()
        mes['dmm_VoutSet'](timeout=5)

    @share.teststep
    def _step_load(self, dev, mes):
        """Measure output voltage under load conditions.

           Load and measure output.
           Check output regulation.
           Check for shutdown with overload.

        """
        dev['dcl'].output(16.0)
        self.measure(
            ('dmm_Vbus', 'dmm_Vbias', 'dmm_SecCtl', 'dmm_SecCtl2',
             'dmm_Vout', ), timeout=5)
        # Measure load regulation
        dev['dcl'].output(0.0)
        noload = mes['dmm_Vout'](timeout=5).reading1
        dev['dcl'].output(24.0)
        fullload = mes['dmm_Vout'](timeout=5).reading1
        reg = ((noload - fullload) / noload) * 100
        mes['dmm_reg'].sensor.store(reg)
        mes['dmm_reg']()
        dev['dcl'].output(30.05, delay=1)
        mes['dmm_VoutOff'](timeout=10)
        dev['acsource'].output(0.0, delay=1)
        dev['dcl'].output(0.0)
        dev['discharge'].pulse(1.0)

    @share.teststep
    def _step_input_ov(self, dev, mes):
        """Check for shutdown with input over voltage."""
        dev['dcl'].output(0.5)
        acs = dev['acsource']
        acs.output(240.0, output=True, delay=0.5)
        self.measure(('dmm_pwmShdnOn', 'dmm_vacShdnOn', ), timeout=8)
        acs.output(300.0, delay=0.5)
        self.measure(('dmm_pwmShdnOff', 'dmm_vacShdnOn', ), timeout=8)
        acs.output(0.0)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcl_a', tester.DCLoad, 'DCL1'),
                ('dcl_b', tester.DCLoad, 'DCL3'),
                ('dcs_SecCtl2', tester.DCSource, 'DCS2'),
                ('dcs_Vout', tester.DCSource, 'DCS3'),
                ('rla_Fuse', tester.Relay, 'RLA4'),
                ('rla_Fan', tester.Relay, 'RLA6'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['dcl'] = tester.DCLoadParallel(
            ((self['dcl_a'], 15.0), (self['dcl_b'], 15.0)))

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl'].output(5.0, delay=1)
        self['discharge'].pulse()
        for dcs in ('dcs_Vout', 'dcs_SecCtl2'):
            self[dcs].output(0.0, False)
        self['dcl'].output(0.0, False)
        for rla in ('rla_Fuse', 'rla_Fan'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oMirReg'] = sensor.MirrorReading()
        self['oLock'] = sensor.Res(dmm, high=17, low=5, rng=10000, res=1)
        self['oFanConn'] = sensor.Res(dmm, high=6, low=6, rng=1000, res=1)
        self['oInrush'] = sensor.Res(dmm, high=1, low=2, rng=1000, res=0.1)
        self['oVout'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self['oSecCtl'] = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.01)
        self['oSecCtl2'] = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.01)
        self['oGreenLed'] = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.01)
        self['oRedLed'] = sensor.Vdc(dmm, high=10, low=3, rng=10, res=0.01)
        self['oFan12V'] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.1)
        self['oSecShdn'] = sensor.Vdc(dmm, high=16, low=3, rng=100, res=0.01)
        self['oVbus'] = sensor.Vdc(dmm, high=3, low=1, rng=1000, res=0.1)
        self['oVbias'] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.1)
        self['oAcDetect'] = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.1)
        self['oVac'] = sensor.Vac(dmm, high=2, low=4, rng=1000, res=0.1)
        self['oPWMShdn'] = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.01)
        self['oVacOVShdn'] = sensor.Vdc(dmm, high=15, low=1, rng=100, res=0.01)
        vout_low, vout_high = self.limits['VoutSet'].limit
        self['oAdjVout'] = sensor.AdjustAnalog(
            sensor=self['oVout'],
            low=vout_low, high=vout_high,
            message=tester.translate('ts3020h_initial', 'AdjR130'),
            caption=tester.translate('ts3020h_initial', 'capAdjOutput'))
        self['oOVP'] = sensor.Ramp(
            stimulus=self.devices['dcs_Vout'],
            sensor=self['oSecShdn'],
            detect_limit=self.limits['inVP'],
            ramp_range=sensor.RampRange(start=14.5, stop=17.0, step=0.05),
            delay=0.1)
        self['oUVP'] = sensor.Ramp(
            stimulus=self.devices['dcs_Vout'],
            sensor=self['oSecShdn'],
            detect_limit=self.limits['inVP'],
            ramp_range=sensor.RampRange(start=11.5, stop=8.0, step=-0.1),
            delay=0.3)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_reg', 'Reg', 'oMirReg', ''),
            ('dmm_Lock', 'FixtureLock', 'oLock', ''),
            ('dmm_FanConn', 'FanConn', 'oFanConn', ''),
            ('dmm_InrushOff', 'InrushOff', 'oInrush', ''),
            ('dmm_InrushOn', 'InrushOn', 'oInrush', ''),
            ('dmm_VoutExt', 'VoutExt', 'oVout', ''),
            ('dmm_VoutPre', 'VoutPre', 'oVout', ''),
            ('dmm_Vout', 'Vout', 'oVout', ''),
            ('dmm_VoutSet', 'VoutSet', 'oVout', ''),
            ('dmm_VoutOff', 'VoutOff', 'oVout', ''),
            ('dmm_SecCtlExt', 'SecCtlExt', 'oSecCtl', ''),
            ('dmm_SecCtl2Ext', 'SecCtl2Ext', 'oSecCtl2', ''),
            ('dmm_SecCtl', 'SecCtl', 'oSecCtl', ''),
            ('dmm_SecCtl2', 'SecCtl2', 'oSecCtl2', ''),
            ('dmm_GreenOn', 'LedOn', 'oGreenLed', ''),
            ('dmm_GreenOff', 'LedOff', 'oGreenLed', ''),
            ('dmm_RedOn', 'LedOn', 'oRedLed', ''),
            ('dmm_RedOff', 'LedOff', 'oRedLed', ''),
            ('dmm_FanOff', 'FanOff', 'oFan12V', ''),
            ('dmm_FanOn', 'FanOn', 'oFan12V', ''),
            ('dmm_VbusExt', 'VbusExt', 'oVbus', ''),
            ('dmm_VbusOff', 'VbusOff', 'oVbus', ''),
            ('dmm_Vbus', 'Vbus', 'oVbus', ''),
            ('dmm_Vbias', 'Vbias', 'oVbias', ''),
            ('dmm_AcDetOff', 'AcDetOff', 'oAcDetect', ''),
            ('dmm_AcDetOn', 'AcDetOn', 'oAcDetect', ''),
            ('dmm_VacMin', 'VacMin', 'oVac', ''),
            ('dmm_Vac', 'Vac', 'oVac', ''),
            ('dmm_SecShdnOff', 'SecShdnOff', 'oSecShdn', ''),
            ('dmm_pwmShdnOn', 'PwmShdnOn', 'oPWMShdn', ''),
            ('dmm_pwmShdnOff', 'PwmShdnOff', 'oPWMShdn', ''),
            ('dmm_vacShdnOn', 'VacShdnOn', 'oVacOVShdn', ''),
            ('dmm_vacShdnOff', 'VacShdnOff', 'oVacOVShdn', ''),
            ('ramp_OVP', 'OVP', 'oOVP', ''),
            ('ramp_UVP', 'UVP', 'oUVP', ''),
            ('ui_AdjVout', 'Notify', 'oAdjVout', ''),
            ))
