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
        tester.LimitDelta('Vsolar', config.vsol, 0.5),
        tester.LimitDelta('Vbat', 14.6, 0.3),
        tester.LimitDelta('Vchem', 2.5, 0.5,
            doc='Voltage present on sense conn'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('Solar', self._step_solar),
            )

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply Aux input power and measure output."""
        dev['dcs_vin'].output(config.vaux, True, delay=0.5)
        dev['dcl_vbat'].output(0.01, output=True)
        self.measure(
            ('dmm_vaux', 'dmm_vbat', 'dmm_vchem'), timeout=5)

    @share.teststep
    def _step_solar(self, dev, mes):
        """Apply Solar input power and measure output."""
        dev['rla_solar'].set_on()
        dev['dcs_vin'].output(config.vsol)
        mes['dmm_vsol'](timeout=5)
        dev['rla_batt'].set_on()
        mes['dmm_vbat'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcl_vbat', tester.DCLoad, 'DCL1'),
                ('rla_solar', tester.Relay, 'RLA1'),
                ('rla_batt', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vin', 'dcl_vbat', ):
            self[dev].output(0.0, False)
        for rla in ('rla_solar', 'rla_batt', ):
            self[rla].set_off()


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
        self['vsol'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vaux', 'Vaux', 'vaux', 'Aux input ok'),
            ('dmm_vbat', 'Vbat', 'vbat', 'Battery output ok'),
            ('dmm_vchem', 'Vchem', 'vchem', 'Sense connector plugged in'),
            ('dmm_vsol', 'Vsolar', 'vsol', 'Solar input ok'),
            ))
