#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Final Test Program."""

import tester
import share

LIMITS = (
    tester.LimitDelta('Vbat', 12.8, 0.2),
    )


class Final(share.TestSequence):

    """BP35 Final Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_powerup),
            )

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit and measure output voltages."""
        dev['acsource'].output(voltage=240.0, output=True)
        mes['dmm_vbat'].measure(timeout=10)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        self['dmm'] = tester.DMM(self.physical_devices['DMM'])
        self['acsource'] = tester.ACSource(self.physical_devices['ACS'])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        self['vbat'] = tester.sensor.Vdc(
            self.devices['dmm'], high=2, low=2, rng=100, res=0.001)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self['dmm_vbat'] = tester.Measurement(
            self.limits['Vbat'], self.sensors['vbat'])
