#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSU360-1TA Initial Test Program."""

import time
import tester
from tester import (
    TestStep,
    LimitLow, LimitBetween, LimitDelta
    )
import share

LIMITS = (
    LimitDelta('ACin', 90, 5),
    LimitBetween('PFC', 389.0, 415.0),
    LimitBetween('PriCtl', 12.0, 14.0),
    LimitBetween('PriVref', 7.3, 7.6),
    LimitBetween('24Vnl', 23.40, 24.60),
    LimitBetween('24Vfl', 23.32, 24.60),
    LimitBetween('Fan12V', 11.4, 12.6),
    LimitBetween('SecCtl', 22.0, 28.0),
    LimitBetween('SecVref', 2.4, 2.6),
    LimitLow('FixtureLock', 20),
    LimitBetween('OCP', 15.2, 21.0),
    LimitLow('inOCP', 23.0),
    )


class Initial(share.TestSequence):

    """GSU360-1TA Initial Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('FixtureLock', self._step_fixture_lock),
            TestStep('PowerUp', self._step_power_up),
            TestStep('FullLoad', self._step_full_load),
            TestStep('OCP', self._step_ocp),
            )

    @share.teststep
    def _step_fixture_lock(self, dev, mes):
        """Check that Fixture Lock is closed."""
        mes['dmm_Lock'](timeout=5)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up unit at 92Vac and measure primary voltages."""
        dev['acsource'].output(92.0, output=True, delay=0.5)
        mes['dmm_ACin'](timeout=5)
        time.sleep(2)
        self.measure(
            ('dmm_PFC', 'dmm_PriCtl', 'dmm_PriVref', 'dmm_24Vnl',
             'dmm_Fan12V', 'dmm_SecCtl', 'dmm_SecVref', ), timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Power up unit at 240Vac, load and measure secondary voltages."""
        dev['acsource'].output(240.0, delay=0.5)
        dev['dcl_24V'].output(15.0, output=True)
        mes['dmm_24Vfl'](timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        mes['ramp_OCP']()


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('dcl_24V', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_24V'].output(5.0, delay=1)
        self['dcl_24V'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['ACin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self['PFC'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self['PriCtl'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self['PriVref'] = sensor.Vdc(dmm, high=5, low=2, rng=10, res=0.001)
        self['o24V'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self['Fan12V'] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self['SecCtl'] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.01)
        self['SecVref'] = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self['Lock'] = sensor.Res(dmm, high=10, low=5, rng=10000, res=0.1)
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl_24V'],
            sensor=self['o24V'],
            detect_limit=(self.limits['inOCP'], ),
            start=15.0, stop=22.0, step=0.05, delay=0.05)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_ACin', 'ACin', 'ACin', ''),
            ('dmm_PFC', 'PFC', 'PFC', ''),
            ('dmm_PriCtl', 'PriCtl', 'PriCtl', ''),
            ('dmm_PriVref', 'PriVref', 'PriVref', ''),
            ('dmm_24Vnl', '24Vnl', 'o24V', ''),
            ('dmm_24Vfl', '24Vfl', 'o24V', ''),
            ('dmm_Fan12V', 'Fan12V', 'Fan12V', ''),
            ('dmm_SecCtl', 'SecCtl', 'SecCtl', ''),
            ('dmm_SecVref', 'SecVref', 'SecVref', ''),
            ('dmm_Lock', 'FixtureLock', 'Lock', ''),
            ('ramp_OCP', 'OCP', 'oOCP', ''),
            ))
