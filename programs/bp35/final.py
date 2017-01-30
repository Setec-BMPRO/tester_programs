#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Final Test Program."""

import tester
from share import teststep, SupportBase, AttributeDict

LIMITS = tester.limitdict((
    tester.LimitHiLoDelta('Vbat', (12.8, 0.2)),
    ))


class Final(tester.TestSequence):

    """BP35 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        super().__init__(selection, None, fifo)
        self.devices = physical_devices
        self.support = None

    def open(self):
        """Prepare for testing."""
        self.support = Support(self.devices)
        sequence = (
            tester.TestStep('PowerUp', self._step_powerup),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.support.reset()

    @teststep
    def _step_powerup(self, sup, dev, mes):
        """Power-Up the Unit and measure output voltages."""
        dev['acsource'].output(voltage=240.0, output=True)
        mes['dmm_vbat'].measure(timeout=10)


class Support(SupportBase):

    """Supporting data."""

    def __init__(self, physical_devices):
        """Create all supporting classes."""
        super().__init__()
        self.devices = LogicalDevices(physical_devices)
        self.limits = LIMITS
        self.sensors = Sensors(self.devices)
        self.measurements = Measurements(self.sensors)


class LogicalDevices(AttributeDict):

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        super().__init__()
        self['dmm'] = tester.DMM(devices['DMM'])
        self['acsource'] = tester.ACSource(devices['ACS'])

    def reset(self):
        """Reset instruments."""
        self['acsource'].output(voltage=0.0, output=False)


class Sensors(AttributeDict):

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used

        """
        super().__init__()
        self['vbat'] = tester.sensor.Vdc(
            logical_devices['dmm'], high=1, low=1, rng=100, res=0.001)


class Measurements(AttributeDict):

    """Measurements."""

    def __init__(self, sense):
        """Create all Measurement instances.

           @param sense Sensors used

        """
        super().__init__()
        self['dmm_vbat'] = tester.Measurement(LIMITS['Vbat'], sense['vbat'])
