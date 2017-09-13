#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE4/5 Final Test Program."""

import tester
from tester import TestStep, LimitLow, LimitBetween, LimitDelta
import share


class Final(share.TestSequence):

    """BCE4/5 Final Test Program."""

    # Limits common to both versions
    _common = (
        LimitDelta('AlarmOpen', 10.0, 1.0, doc='Contacts open'),
        LimitLow('AlarmClosed', 1.0, doc='Contacts closed'),
        LimitBetween('Dropout', 150.0, 180.0, doc='AC dropout voltage'),
        )
    # Test limit selection keyed by program parameter
    limitdata = {
        '4': {
            'Limits': _common + (
                LimitBetween('VoutNL', 13.50, 13.80),
                LimitBetween('Vout', 13.28, 13.80),
                LimitBetween('Vbat', 13.28, 13.92),
                LimitLow('inOCP', 13.28),
                LimitBetween('OCP', 10.2, 13.0),
                LimitLow('InDropout', 13.28),
                ),
            'FullLoad': 10.1,
            'OCPramp': (10.0, 13.5),
            },
        '5': {
            'Limits': _common + (
                LimitBetween('VoutNL', 27.00, 27.60),
                LimitBetween('Vout', 26.56, 27.84),
                LimitBetween('Vbat', 26.56, 27.84),
                LimitLow('inOCP', 26.56),
                LimitBetween('OCP', 5.1, 6.3),
                LimitLow('InDropout', 26.56),
                ),
            'FullLoad': 5.1,
            'OCPramp': (5.0, 7.0),
            },
        }

    def open(self):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('FullLoad', self._step_full_load),
            TestStep('OCP', self._step_ocp),
            TestStep('LowMains', self._step_low_mains),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit."""
        dev['dcs_10Vfixture'].output(10.0, output=True)
        mes['dmm_AlarmClosed'](timeout=5)
        self.dcload((('dcl_Vout', 0.1), ('dcl_Vbat', 0.0)), output=True)
        dev['acsource'].output(185.0, output=True, delay=0.5)
        mes['dmm_VoutNL'](timeout=5)
        dev['acsource'].output(240.0, delay=0.5)
        self.measure(
            ('dmm_VoutNL', 'dmm_Vbat', 'dmm_AlarmOpen'),
            timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        self.dcload(
            (('dcl_Vout', self.limitdata[self.parameter]['FullLoad']),
            ('dcl_Vbat', 0.1)), )
        self.measure(('dmm_Vout', 'dmm_Vbat'), timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        # Load is already at FullLoad
        mes['ramp_OCP']()

    @share.teststep
    def _step_low_mains(self, dev, mes):
        """Low input voltage."""
        dev['acsource'].output(185.0, delay=0.5)
        self.measure(('dmm_Vout', 'dropout', ))


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcs_10Vfixture', tester.DCSource, 'DCS2'),
                ('dcl_Vout', tester.DCLoad, 'DCL1'),
                ('dcl_Vbat', tester.DCLoad, 'DCL2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcs_10Vfixture'].output(0.0, output=False)
        self['dcl_Vout'].output(5.0, delay=0.5)
        for dcl in ('dcl_Vout', 'dcl_Vbat'):
            self[dcl].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oVout'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['oVbat'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['oAlarm'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        ocp_start, ocp_stop = Final.limitdata[self.parameter]['OCPramp']
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl_Vout'],
            sensor=self['oVout'],
            detect_limit=(self.limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)
        self['oDropout'] = sensor.Ramp(
            stimulus=self.devices['acsource'],
            sensor=self['oVout'],
            detect_limit=(self.limits['InDropout'], ),
            start=185.0, stop=150.0, step=-0.5, delay=0.1, reset=False)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_VoutNL', 'VoutNL', 'oVout', ''),
            ('dmm_Vout', 'Vout', 'oVout', ''),
            ('dmm_Vbat', 'Vbat', 'oVbat', ''),
            ('dmm_AlarmOpen', 'AlarmOpen', 'oAlarm', ''),
            ('dmm_AlarmClosed', 'AlarmClosed', 'oAlarm', ''),
            ('ramp_OCP', 'OCP', 'oOCP', ''),
            ('dropout', 'Dropout', 'oDropout', ''),
            ))
