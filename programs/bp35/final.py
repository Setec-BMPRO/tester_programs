#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Final Test Program."""

import tester
from tester import TestStep, LimitHiLoDelta
import share

LIMITS = tester.limitdict((
    LimitHiLoDelta('Vbat', (12.8, 0.2)),
    ))


class Final(share.Support, tester.TestSequence):

    """BP35 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        devices = LogicalDevices(physical_devices)
        limits = LIMITS
        sensors = Sensors(devices)
        measurements = Measurements(sensors, limits)
        sequence = (
            TestStep('PowerUp', self._step_powerup),
            )
        tester.TestSequence.__init__(self, selection, sequence, fifo)
        share.Support.__init__(self, devices, limits, sensors, measurements)

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
        self['acsource'].output(voltage=0.0, output=False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        self['vbat'] = tester.sensor.Vdc(
            self.devices['dmm'], high=1, low=1, rng=100, res=0.001)


class Measurements(share.AttributeDict):

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurements.

        @param sense Sensors
        @param limits Test limits

        """
        super().__init__()
        self.sense = sense
        self.limits = limits

    def open(self):
        """Create all Measurements."""
        self['dmm_vbat'] = tester.Measurement(
            self.limits['Vbat'], self.sense['vbat'])
