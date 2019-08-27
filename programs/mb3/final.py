#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Final Program."""

import tester

import share
from . import config


class Final(share.TestSequence):

    """MB3 Final Test Program."""

    limitdata = (
        tester.LimitDelta('Vaux', config.vaux, 0.5),
        tester.LimitDelta('Vbat', 14.6, 0.3),
        tester.LimitDelta('Vchem', 2.5, 0.5,
            doc='Voltage present on sense conn'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerOn', self._step_power_on),
            )

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply input power and measure voltages."""
        dev['dcs_vaux'].output(config.vaux, True, delay=0.5)
        dev['dcl_vbat'].output(0.01, output=True)
        self.measure(
            ('dmm_vaux', 'dmm_vbat', 'dmm_vchem'), timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vaux', tester.DCSource, 'DCS2'),
                ('dcl_vbat', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vaux', 'dcl_vbat', ):
            self[dev].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vaux'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self['vbat'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self['vchem'] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.01)
        self['vchem'].doc = 'X5, pin1'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vaux', 'Vaux', 'vaux', 'Aux input ok'),
            ('dmm_vbat', 'Vbat', 'vbat', 'Battery output ok'),
            ('dmm_vchem', 'Vchem', 'vchem', 'Sense connector plugged in'),
            ))
