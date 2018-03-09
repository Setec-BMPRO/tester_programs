#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UNI-750 Final Test Program."""

import tester
from tester import TestStep, LimitLow, LimitBetween, LimitDelta
import share


class Final(share.TestSequence):

    """UNI-750 Final Test Program."""

    limitdata = (
        LimitDelta('AcUnsw', 240, 10),
        LimitLow('AcSwOff', 0.5),
        LimitDelta('AcSwOn', 240, 10),
        LimitBetween('24V', 23.256, 24.552),
        LimitBetween('24Vfl', 23.5, 24.3),
        LimitDelta('15V', 15.0, 0.75),
        LimitDelta('12V', 12.0, 0.6),
        LimitBetween('5V', 5.0, 5.212),
        LimitBetween('3.3V', 3.25, 3.423),
        LimitBetween('5Vi', 4.85, 5.20),
        LimitBetween('PGood', 5.0, 5.25),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('PowerOn', self._step_power_on),
            TestStep('FullLoad', self._step_full_load),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Connect unit to 240Vac, Remote AC Switch off."""
        dev['acsource'].output(240.0, output=True, delay=0.5)
        self.measure(('dmm_AcUnsw', 'dmm_AcSwOff', ), timeout=5)

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Remote AC Switch on, measure outputs at min load."""
        self.dcload(
            (('dcl_24V', 3.0), ('dcl_15V', 1.0), ('dcl_12V', 2.0),
             ('dcl_5V', 1.0), ('dcl_3V3', 1.0)), output=True)
        dev['dcs_PwrOn'].output(12.0, output=True)
        self.measure(
            ('dmm_AcSwOn', 'ui_YesNoFan', 'dmm_24V', 'dmm_15V', 'dmm_12V',
             'dmm_5V', 'dmm_3V3', 'dmm_5Vi', 'dmm_PGood', ), timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure outputs at full-load."""
        self.dcload(
            (('dcl_24V', 13.5), ('dcl_15V', 7.5), ('dcl_12V', 20.0),
             ('dcl_5V', 10.0), ('dcl_3V3', 5.0)))
        self.measure(
            ('dmm_24V', 'dmm_15V', 'dmm_12V', 'dmm_5V', 'dmm_3V3', 'dmm_5Vi',
             'dmm_PGood', ), timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                # This DC Source drives the Remote AC Switch
                ('dcs_PwrOn', tester.DCSource, 'DCS2'),
                ('dcl_24V', tester.DCLoad, 'DCL1'),
                ('dcl_15V', tester.DCLoad, 'DCL2'),
                ('dcl_12V', tester.DCLoad, 'DCL3'),
                ('dcl_5V', tester.DCLoad, 'DCL4'),
                ('dcl_3V3', tester.DCLoad, 'DCL5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcs_PwrOn'].output(0.0, output=False)
        for load in ('dcl_24V', 'dcl_15V', 'dcl_12V', 'dcl_5V', 'dcl_3V3'):
            self[load].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oAcUnsw'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self['oAcSw'] = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.1)
        self['o24V'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['o15V'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['o12V'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['o5V'] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self['o3V3'] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.001)
        self['o5Vi'] = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self['oPGood'] = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.01)
        self['oYesNoFan'] = sensor.YesNo(
            message=tester.translate('uni750_final', 'IsFanOn?'),
            caption=tester.translate('uni750_final', 'capFan'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_AcUnsw', 'AcUnsw', 'oAcUnsw', ''),
            ('dmm_AcSwOff', 'AcSwOff', 'oAcSw', ''),
            ('dmm_AcSwOn', 'AcSwOn', 'oAcSw', ''),
            ('dmm_24V', '24V', 'o24V', ''),
            ('dmm_24Vfl', '24Vfl', 'o24V', ''),
            ('dmm_15V', '15V', 'o15V', ''),
            ('dmm_12V', '12V', 'o12V', ''),
            ('dmm_5V', '5V', 'o5V', ''),
            ('dmm_3V3', '3.3V', 'o3V3', ''),
            ('dmm_5Vi', '5Vi', 'o5Vi', ''),
            ('dmm_PGood', 'PGood', 'oPGood', ''),
            ('ui_YesNoFan', 'Notify', 'oYesNoFan', ''),
            ))
