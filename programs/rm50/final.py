#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RM-50-24 Final Test Program."""

import tester
from tester import TestStep, LimitLow, LimitHigh, LimitBetween, LimitDelta
import share


class Final(share.TestSequence):

    """RM-50-24 Final Test Program."""

    limits = (
        LimitDelta('Rsense', 1000, 20),
        LimitLow('Vsense', 0.0001),
        LimitLow('uSwitch', 100),
        LimitLow('Vdrop', 0.4),
        LimitBetween('24Vdcin', 23.0, 24.4),
        LimitBetween('24Vdcout', 23.6, 24.4),
        LimitLow('24Voff', 1.0),
        LimitBetween('24Vnl', 23.6, 24.4),
        LimitBetween('24Vfl', 23.4, 24.1),
        LimitBetween('24Vpl', 23.0, 24.1),
        LimitBetween('OCP', 3.2, 4.3),
        LimitLow('inOCP', 23.0),
        LimitLow('CurrShunt', 2.5),
        LimitBetween('PowNL', 1.0, 5.0),
        LimitBetween('PowFL', 40.0, 70.0),
        LimitHigh('Eff', 84.0),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limits, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('FixtureLock', self._step_fixture_lock),
            TestStep('DCInputLeakage', self._step_dcinput_leakage),
            TestStep('DCInputTrack', self._step_dcinput_track),
            TestStep('ACInput240V', self._step_acinput240v),
            TestStep('ACInput110V', self._step_acinput110v),
            TestStep('ACInput90V', self._step_acinput90v),
            TestStep('OCP', self._step_ocp),
            TestStep('PowerNoLoad', self._step_power_noload),
            TestStep('Efficiency', self._step_efficiency),
            )

    @share.teststep
    def _step_fixture_lock(self, dev, mes):
        """Check that Fixture Lock is closed."""
        mes['dmm_Lock'](timeout=5)

    @share.teststep
    def _step_dcinput_leakage(self, dev, mes):
        """Test for input leakage current at the DC input with no load."""
        mes['dmm_Rsense'](timeout=5)
        dev['rla_rsense'].set_on()
        dev['dcs_24V'].output(24.0, output=True)
        mes['dmm_Vsense'](timeout=5)

    @share.teststep
    def _step_dcinput_track(self, dev, mes):
        """
        Measure the drop in the track between dc input and output at full load.
        """
        dev['dcl_dcout'].output(2.1, True)
        val = mes['dmm_24Vdcin'](timeout=5).reading1
        # Slightly higher dc input to compensate for drop in fixture cabling
        dev['dcs_24V'].output(24.0 + (24.0 - val))
        vals = self.measure(
            ('dmm_24Vdcin', 'dmm_24Vdcout'), timeout=5).readings
        mes['dmm_vdcDrop'].sensor.store(vals[0] - vals[1])
        mes['dmm_vdcDrop']()
        dev['dcs_24V'].output(0.0, output=False)
        dev['dcl_dcout'].output(0.0)

    @share.teststep
    def _step_acinput240v(self, dev, mes):
        """Apply 240V AC input and measure output at no load and full load."""
        self._ac_reg(dev, mes, 240, 50)

    @share.teststep
    def _step_acinput110v(self, dev, mes):
        """Apply 110V AC input and measure output at no load and full load."""
        self._ac_reg(dev, mes, 110, 60)

    @share.teststep
    def _step_acinput90v(self, dev, mes):
        """Apply 90V AC input and measure outputs at various load steps."""
        self._ac_reg(dev, mes, 90, 60)
        dev['dcl_out'].linear(2.7, 2.95, step=0.05, delay=0.05)
        for curr in (3.0, 3.05):
            with tester.PathName(str(curr)):
                dev['dcl_out'].output(curr, delay=0.5)
                mes['dmm_24Vpl'](timeout=5)

    @staticmethod
    def _ac_reg(dev, mes, acv, acf):
        """Apply 90V AC input and measure outputs at various load steps."""
        dev['dcl_out'].output(0.0, output=True)
        dev['acsource'].output(
            voltage=acv, frequency=acf, output=True, delay=0.5)
        mes['dmm_24Vnl'](timeout=5)
        dev['dcl_out'].output(2.1)
        mes['dmm_24Vfl'](timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point, turn off and recover."""
        dev['acsource'].output(240.0, frequency=50, delay=0.5)
        self.measure(('dmm_24Vpl', 'ramp_OCP', ), timeout=5)
        dev['acsource'].output(0.0)
        dev['dcl_out'].output(2.1, delay=1)
        mes['dmm_24Voff'](timeout=5)

    @share.teststep
    def _step_power_noload(self, dev, mes):
        """Measure input power at no load."""
        dev['acsource'].output(240.0, delay=0.5)
        dev['dcl_out'].output(0.05, delay=0.5)
        self.measure(('dmm_24Vnl', 'dmm_powerNL', ), timeout=5)

    @share.teststep
    def _step_efficiency(self, dev, mes):
        """Measure efficiency."""
        dev['dcl_out'].output(2.1)
        inp_pwr_fl = mes['dmm_powerFL'](timeout=5).reading1
        out_volts_fl = mes['dmm_24Vfl'](timeout=5).reading1
        out_curr_fl = mes['dmm_currShunt'](timeout=5).reading1
        eff = 100 * out_volts_fl * out_curr_fl / inp_pwr_fl
        mes['dmm_eff'].sensor.store(eff)
        mes['dmm_eff']()


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('pwr', tester.Power, 'PWR'),
                ('dcs_24V', tester.DCSource, 'DCS2'),
                ('dcl_out', tester.DCLoad, 'DCL1'),
                ('dcl_dcout', tester.DCLoad, 'DCL5'),
                ('rla_rsense', tester.Relay, 'RLA1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_out'].output(2.1, delay=1)
        self['dcs_24V'].output(0.0, False)
        for load in ('dcl_out', 'dcl_dcout'):
            self[load].output(0.0, False)
        self['rla_rsense'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        pwr = self.devices['pwr']
        sensor = tester.sensor
        self['oMirVdcDrop'] = sensor.Mirror()
        self['oMirPowNL'] = sensor.Mirror()
        self['oMirEff'] = sensor.Mirror()
        self['Lock'] = sensor.Res(dmm, high=9, low=5, rng=10000, res=1)
        self['oRsense'] = sensor.Res(dmm, high=1, low=1, rng=10000, res=1)
        self['oVsense'] = sensor.Vdc(
            dmm, high=1, low=1, rng=1, res='MAX', scale=0.001)
        self['o24Vdcin'] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self['o24Vdcout'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['o24V'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['oCurrshunt'] = sensor.Vdc(
            dmm, high=5, low=4, rng=0.1, res='MAX', scale=1000, nplc=100)
        self['oInputPow'] = sensor.Power(pwr)
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl_out'],
            sensor=self['o24V'],
            detect_limit=(self.limits['inOCP'], ),
            start=3.05, stop=4.4, step=0.05, delay=0.1)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vdcDrop', 'Vdrop', 'oMirVdcDrop', ''),
            ('dmm_eff', 'Eff', 'oMirEff', ''),
            ('dmm_Lock', 'uSwitch', 'Lock', ''),
            ('dmm_Rsense', 'Rsense', 'oRsense', ''),
            ('dmm_Vsense', 'Vsense', 'oVsense', ''),
            ('dmm_24Vdcin', '24Vdcin', 'o24Vdcin', ''),
            ('dmm_24Vdcout', '24Vdcout', 'o24Vdcout', ''),
            ('dmm_24Voff', '24Voff', 'o24V', ''),
            ('dmm_24Vnl', '24Vnl', 'o24V', ''),
            ('dmm_24Vfl', '24Vfl', 'o24V', ''),
            ('dmm_24Vpl', '24Vpl', 'o24V', ''),
            ('dmm_currShunt', 'CurrShunt', 'oCurrshunt', ''),
            ('dmm_powerNL', 'PowNL', 'oInputPow', ''),
            ('dmm_powerFL', 'PowFL', 'oInputPow', ''),
            ('ramp_OCP', 'OCP', 'oOCP', ''),
            ))
