#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""J35 Final Test Program."""

import tester
import share
from tester import (
    TestStep,
    LimitLo, LimitHi, LimitHiLo, LimitHiLoDelta, LimitHiLoPercent
    )

_COMMON = (
    LimitLo('FanOff', 1.0),
    LimitHi('FanOn', 10.0),
    LimitHiLoDelta('Vout', (12.8, 0.2)),
    LimitHiLoPercent('Vload', (12.8, 5)),
    LimitLo('InOCP', 11.6),
    )

LIMITS_A = _COMMON + (
    LimitHiLo('OCP', (20.0, 25.0)),
    )

LIMITS_BC = _COMMON + (
    LimitHiLo('OCP', (35.0, 42.0)),
    )

CONFIG = {      # Test configuration keyed by program parameter
    'A': {
        'Limits': LIMITS_A,
        'LoadCount': 7,
        },
    'B': {
        'Limits': LIMITS_BC,
        'LoadCount': 14,
        },
    'C': {
        'Limits': LIMITS_BC,
        'LoadCount': 14,
        },
    }


class Final(share.TestSequence):

    """J35 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(
            CONFIG[self.parameter]['Limits'],
            LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_powerup),
            TestStep('Load', self._step_load),
            TestStep('OCP', self._step_ocp),
            )
        self.load_count = CONFIG[self.parameter]['LoadCount']

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac and measure output voltage."""
        dev['dcs_photo'].output(12.0, True)
        mes['dmm_fanoff'](timeout=5)
        dev['acsource'].output(240.0, output=True)
        mes['dmm_fanon'](timeout=15)
        for load in range(self.load_count):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['dmm_vouts'][load](timeout=5)

    @share.teststep
    def _step_load(self, dev, mes):
        """Test outputs with load."""
        dev['dcl_out'].output(0.0,  output=True)
        dev['dcl_out'].binary(1.0, self.load_count * 2.0, 5.0)
        for load in range(self.load_count):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['dmm_vloads'][load](timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        mes['ramp_ocp'](timeout=5)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcs_photo', tester.DCSource, 'DCS1'),
                ('dcl_out', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].output(voltage=0.0, output=False)
        self['dcs_photo'].output(0.0, False)
        self['dcl_out'].output(0.0, False)

class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['photo'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self['vload1'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        low, high = self.limits['OCP'].limit
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl_out'], sensor=self['vload1'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - 1, stop=high + 1, step=0.5, delay=0.2)
        # Generate load voltage sensors
        vloads = []
        for i in range(CONFIG[self.parameter]['LoadCount']):
            s = sensor.Vdc(dmm, high=i + 5, low=3, rng=100, res=0.001)
            vloads.append(s)
        self['vloads'] = vloads


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_fanoff', 'FanOff', 'photo'),
            ('dmm_fanon', 'FanOn', 'photo'),
            ('ramp_ocp', 'OCP', 'ocp'),
            ))
        # Generate load measurements
        vouts = []
        vloads = []
        for sen in self.sensors['vloads']:
            vouts.append(tester.Measurement(self.limits['Vout'], sen))
            vloads.append(tester.Measurement(self.limits['Vload'], sen))
        self['dmm_vouts'] = vouts
        self['dmm_vloads'] = vloads
