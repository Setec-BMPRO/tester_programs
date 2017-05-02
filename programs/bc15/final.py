#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Test Program."""

import tester
from tester import (
    LimitLow, LimitDelta, LimitPercent, LimitBoolean
    )
import share

LIMITS = (
    LimitBoolean('Notify', True),
    LimitPercent('VoutNL', 13.85, 1.0),
    LimitPercent('Vout', 13.85, 5.0),
    LimitLow('InOCP', 12.0),
    LimitDelta('OCP', 14.0, 2.0),
    )


class Final(share.TestSequence):

    """BC15 Final Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerOn', self._step_poweron),
            tester.TestStep('Load', self._step_loaded),
            )

    @share.teststep
    def _step_poweron(self, dev, mes):
        """Power up the Unit and measure output with min load."""
        dev['dcl'].output(1.0, output=True)
        dev['acsource'].output(240.0, output=True)
        self.measure(('ps_mode', 'vout_nl', ), timeout=5)

    @share.teststep
    def _step_loaded(self, dev, mes):
        """Load the Unit."""
        dev['dcl'].output(10.0)
        self.measure(('vout', 'ocp', 'ch_mode', ), timeout=5)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ('dmm', tester.DMM, 'DMM'),
            ('acsource', tester.ACSource, 'ACS'),
            ('dcl', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl'].output(0.0, False)
        super().close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vout'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['ps_mode'] = sensor.Notify(
            message=tester.translate('bc15_final', 'GoToPsMode'),
            caption=tester.translate('bc15_final', 'capPsMode'))
        self['ch_mode'] = sensor.Notify(
            message=tester.translate('bc15_final', 'GoToChargeMode'),
            caption=tester.translate('bc15_final', 'capChargeMode'))
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl'],
            sensor=self['vout'],
            detect_limit=(self.limits['InOCP'], ),
            start=10.0, stop=17.0, step=0.5, delay=0.1)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('vout_nl', 'VoutNL', 'vout', ''),
            ('vout', 'Vout', 'vout', ''),
            ('ps_mode', 'Notify', 'ps_mode', ''),
            ('ch_mode', 'Notify', 'ch_mode', ''),
            ('ocp', 'OCP', 'ocp', ''),
            ))
