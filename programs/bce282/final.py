#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Final Program."""

import tester
from tester import TestStep, LimitLow, LimitBetween, LimitDelta
import share


class Final(share.TestSequence):

    """BCE282-12/24 Final Test Program."""

    # Limits common to both versions
    _common = (
        LimitDelta('AlarmOpen', 10000, 1000, doc='Contacts open'),
        LimitLow('AlarmClosed', 100, doc='Contacts closed'),
        )
    # Test limit selection keyed by program parameter
    limitdata = {
        '12': {
            'Limits': _common + (
                LimitDelta('VoutNL', 13.55, 0.20, doc='Output at no load'),
                LimitBetween('VbatNL', 13.20, 13.75, doc='Output at no load'),
                LimitBetween('Vout', 12.98, 13.75, doc='Output with load'),
                LimitBetween('Vbat', 12.98, 13.75, doc='Output with load'),
                LimitLow('inOCP', 12.98, doc='OCP active'),
                LimitBetween('OCPLoad', 20.0, 25.0, doc='OCP point'),
                LimitBetween('OCPBatt', 10.0, 12.0, doc='OCP point'),
                ),
            'FullLoad': 20.1,
            'OCPrampLoad': (20.0, 25.5),
            'OCPrampBatt': (10.0, 12.5),
            },
        '24': {
            'Limits': _common + (
                LimitDelta('VoutNL', 27.60, 0.25, doc='Output at no load'),
                LimitBetween('VbatNL', 27.35, 27.85, doc='Output at no load'),
                LimitBetween('Vout', 26.80, 27.85, doc='Output with load'),
                LimitBetween('Vbat', 26.80, 27.85, doc='Output with load'),
                LimitLow('inOCP', 26.80, doc='OCP active'),
                LimitBetween('OCPLoad', 10.0, 13.0, doc='OCP point'),
                LimitBetween('OCPBatt', 5.0, 6.0, doc='OCP point'),
                ),
            'FullLoad': 10.1,
            'OCPrampLoad': (10.0, 13.5),
            'OCPrampBatt': (5.0, 6.5),
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
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit."""
        mes['AlarmClosed'](timeout=5)
        dev['acsource'].output(voltage=200.0, output=True, delay=0.5)
        self.dcload((('dcl_Vout', 0.1), ('dcl_Vbat', 0.0)), output=True)
        mes['VoutNL'](timeout=5)
        dev['acsource'].output(voltage=240.0, delay=0.5)
        self.measure(('VoutNL', 'VbatNL', 'AlarmOpen'), timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        dev['dcl_Vbat'].output(0.5)
        mes['YesNoGreen']()
        self.dcload(
            (('dcl_Vbat', 0.0),
             ('dcl_Vout', self.limitdata[self.parameter]['FullLoad'])))
        self.measure(('Vout', 'Vbat'), timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        mes['OCPLoad']()
        dev['dcl_Vout'].output(0.0)
        mes['OCPBatt']()
        dev['dcl_Vbat'].output(0.0)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl_Vout', tester.DCLoad, 'DCL1'),
                ('dcl_Vbat', tester.DCLoad, 'DCL2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_Vout'].output(10.0, output=True, delay=0.5)
        for dcl in ('dcl_Vout', 'dcl_Vbat'):
            self[dcl].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['Vout'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['Vout'].doc = 'Load output'
        self['Vbat'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['Vbat'].doc = 'Battery output'
        self['Alarm'] = sensor.Res(dmm, high=5, low=3, rng=100000, res=1)
        self['Alarm'].doc = 'Alarm output contacts'
        self['YesNoGreen'] = sensor.YesNo(
            message=tester.translate('bce282_final', 'IsGreenFlash?'),
            caption=tester.translate('bce282_final', 'capLedGreen'))
        self['YesNoGreen'].doc = 'Operator response'
        ocp_start, ocp_stop = Final.limitdata[self.parameter]['OCPrampLoad']
        self['OCPLoad'] = sensor.Ramp(
            stimulus=self.devices['dcl_Vout'],
            sensor=self['Vout'],
            detect_limit=(self.limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)
        self['OCPLoad'].doc = 'Load OCP point'
        ocp_start, ocp_stop = Final.limitdata[self.parameter]['OCPrampBatt']
        self['OCPBatt'] = sensor.Ramp(
            stimulus=self.devices['dcl_Vbat'],
            sensor=self['Vbat'],
            detect_limit=(self.limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.1)
        self['OCPBatt'].doc = 'Battery OCP point'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('VoutNL', 'VoutNL', 'Vout', ''),
            ('VbatNL', 'VbatNL', 'Vbat', ''),
            ('Vout', 'Vout', 'Vout', ''),
            ('Vbat', 'Vbat', 'Vbat', ''),
            ('AlarmClosed', 'AlarmClosed', 'Alarm', ''),
            ('AlarmOpen', 'AlarmOpen', 'Alarm', ''),
            ('OCPLoad', 'OCPLoad', 'OCPLoad', ''),
            ('OCPBatt', 'OCPBatt', 'OCPBatt', ''),
            ('YesNoGreen', 'Notify', 'YesNoGreen', 'Green LED flashing'),
            ))
