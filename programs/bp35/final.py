#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Final Test Program."""

import tester
import share


class Final(share.TestSequence):

    """BP35 Final Test Program."""

    limitdata = (
        tester.LimitDelta('Vbat', 12.8, 0.2, doc='Output voltage'),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_powerup),
            )

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit and measure output voltages."""
        dev['acsource'].output(voltage=240.0, output=True)
        self.measure(('dmm_vbat', 'ui_yesnogreen',), timeout=10)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        self['dmm'] = tester.DMM(self.physical_devices['DMM'])
        self['acsource'] = tester.ACSource(self.physical_devices['ACS'])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['vbat'] = tester.sensor.Vdc(
            self.devices['dmm'], high=2, low=2, rng=100, res=0.001)
        self['vbat'].doc = 'Unit output'
        self['yesnogreen'] = sensor.YesNo(
            message=tester.translate('bp35_final', 'IsOutputLedGreen?'),
            caption=tester.translate('bp35_final', 'capOutputLed'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vbat', 'Vbat', 'vbat', 'Output ok'),
            ('ui_yesnogreen', 'Notify', 'yesnogreen', 'LED Green'),
            ))
