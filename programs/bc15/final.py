#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Test Program."""

import tester
from tester import LimitLow, LimitDelta
import share

OCP_NOMINAL = 10.0


class Final(share.TestSequence):

    """BC15 Final Test Program."""

    limitdata = (
        LimitDelta('VoutNL', 13.6, 0.3),
        LimitDelta('Vout', 13.6, 0.7),
        LimitLow('InOCP', 12.5),
        LimitDelta('OCP', OCP_NOMINAL, 1.0),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, LogicalDevices, Sensors, Measurements)
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
            start=OCP_NOMINAL - 1.0,
            stop=OCP_NOMINAL + 2.0,
            step=0.1,
            delay=0.2)


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
