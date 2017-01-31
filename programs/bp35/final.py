#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Final Test Program."""

import tester
import share

LIMITS = tester.limitdict((
    tester.LimitHiLoDelta('Vbat', (12.8, 0.2)),
    ))


class Final(share.TestSequence):

    """BP35 Final Test Program."""

    def __init__(self, per_panel, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        devices = LogicalDevices(physical_devices)
        limits = LIMITS
        sensors = Sensors(devices)
        measurements = Measurements(sensors, limits)
        sequence = (
            tester.TestStep('PowerUp', self._step_powerup),
            )
        sequence_data = share.TestSequenceData(
            fifo, per_panel, devices, limits, sensors, measurements, sequence)
        super().__init__(sequence_data)

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


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self['dmm_vbat'] = tester.Measurement(
            self.limits['Vbat'], self.sense['vbat'])
