#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""J35 Final Test Program."""

import tester
import share
from tester import TestStep, LimitLow, LimitHigh, LimitDelta, LimitPercent


class Final(share.TestSequence):

    """J35 Final Test Program."""

    # Load on each output channel
    load_per_output = 2.0
    # Test limits common to all versions
    _common = (
        LimitLow('FanOff', 1.0, doc='No airflow seen'),
        LimitHigh('FanOn', 10.0, doc='Airflow seen'),
        LimitDelta('Vout', 12.8, delta=0.2, doc='No load output voltage'),
        LimitPercent('Vload', 12.8, percent=5, doc='Loaded output voltage'),
        LimitLow('InOCP', 11.6, doc='Output voltage to detect OCP'),
        )
    # Test limits common to the -B and -C versions
    limits_bc = (
        LimitPercent('OCP', 35.0, (4.0, 7.0), doc='OCP trip current'),
        )
    # Test configuration keyed by program parameter
    limitdata = {
        'A': {
            'Limits': _common + (
                LimitPercent('OCP', 20.0, (4.0, 10.0), doc='OCP trip current'),
                ),
            'LoadCount': 7,
            },
        'B': {
            'Limits': _common + limits_bc,
            'LoadCount': 14,
            },
        'C': {
            'Limits': _common + limits_bc,
            'LoadCount': 14,
            },
        }

    def open(self):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]['Limits'],
            LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_powerup),
            TestStep('Load', self._step_load),
            TestStep('OCP', self._step_ocp),
            )
        self.load_count = self.limitdata[self.parameter]['LoadCount']

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac and measure output voltage."""
        mes['dmm_fanoff'](timeout=5)
        dev['acsource'].output(240.0, output=True)
        mes['dmm_fanon'](timeout=15)
        for load in range(self.load_count):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['dmm_vouts'][load](timeout=5)

    @share.teststep
    def _step_load(self, dev, mes):
        """Test outputs with load."""
        dev['dcl_out'].output(1.0,  output=True)
        dev['dcl_out'].binary(1.0, self.load_count * self.load_per_output, 5.0)
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
        for name, devtype, phydevname, doc in (
                ('dmm', tester.DMM, 'DMM',
                 ''),
                ('acsource', tester.ACSource, 'ACS',
                 'AC input power'),
                ('dcs_photo', tester.DCSource, 'DCS3',
                 'Power to airflow detector'),
                ('dcl_out', tester.DCLoad, 'DCL1',
                 'Load shared by all outputs'),
            ):
            self[name] = devtype(self.physical_devices[phydevname], doc)
        self['dcs_photo'].output(12.0, True)
        self.add_closer(lambda: self['dcs_photo'].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_out'].output(15.0, delay=2)
        self['dcl_out'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['photo'] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self['photo'].doc = 'Airflow detector'
        # Generate load voltage sensors
        vloads = []
        for i in range(Final.limitdata[self.parameter]['LoadCount']):
            s = sensor.Vdc(dmm, high=i + 5, low=3, rng=100, res=0.001)
            s.doc = 'Output #{0}'.format(i + 1)
            vloads.append(s)
        self['vloads'] = vloads
        low, high = self.limits['OCP'].limit
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl_out'], sensor=self['vloads'][0],
            detect_limit=(self.limits['InOCP'], ),
            start=low - 1, stop=high + 1, step=0.1, delay=0.1)
        self['ocp'].doc = 'OCP trip value'
        self['ocp'].units = 'Adc'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_fanoff', 'FanOff', 'photo', 'Fan not running'),
            ('dmm_fanon', 'FanOn', 'photo', 'Fan running'),
            ('ramp_ocp', 'OCP', 'ocp', 'Output OCP'),
            ))
        # Generate load measurements
        vouts = []
        vloads = []
        for sen in self.sensors['vloads']:
            vouts.append(tester.Measurement(
                self.limits['Vout'], sen, doc='No load output voltage'))
            vloads.append(tester.Measurement(
                self.limits['Vload'], sen, doc='Loaded output voltage'))
        self['dmm_vouts'] = vouts
        self['dmm_vloads'] = vloads
