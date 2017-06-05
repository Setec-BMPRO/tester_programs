#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Initial Program."""

import tester
from tester import (
    TestStep,
    LimitDelta, LimitBoolean
    )
import share

LIMITS = (
    LimitDelta('Vin', 12.0, 0.5),
    LimitDelta('3V3', 3.3, 0.25),
    LimitBoolean('Notify', True),
    )


class Initial(share.TestSequence):

    """BC2 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        dev['dcs_vin'].output(12.0, True)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_3v3', '3V3', '3v3', ''),
            ))
