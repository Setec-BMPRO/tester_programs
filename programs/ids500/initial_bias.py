#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""IDS-500 Bias Initial Test Program."""

import tester

import share


class InitialBias(share.TestSequence):

    """IDS-500 Initial Bias Test Program."""

    # Test limits
    limitdata = (
        tester.LimitDelta('400V', 390, 410),
        tester.LimitBetween('PVcc', 12.8, 14.5),
        tester.LimitBetween('12VsbRaw', 12.7, 13.49),
        tester.LimitLow('InOCP', 12.6),
        tester.LimitBetween('OCP', 1.2, 2.1),
        tester.LimitLow('FixtureLock', 20),
        )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('OCP', self._step_ocp),
            )

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Check Fixture Lock, power up internal IDS-500 for 400V rail."""
        mes['dmm_lock'](timeout=5)
        dev['acsource'].output(voltage=240.0, output=True)
        self.measure(('dmm_400V', 'dmm_pvcc', ),timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP."""
        dev['dcl_12Vsbraw'].output(0.0, True)
        self.measure(
            ('dmm_12Vsbraw', 'ramp_OCP', 'dmm_12Vsbraw2',), timeout=1)


class Devices(share.Devices):

    """Bias Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_fan', tester.DCSource, 'DCS5'),
                ('dcl_12Vsbraw', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset(delay=2)
        self['discharge'].pulse()
        self['dcs_fan'].output(0.0, False)
        self['dcl_12Vsbraw'].output(0.0, False)


class Sensors(share.Sensors):

    """Bias Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['olock'] = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self['o400V'] = sensor.Vdc(dmm, high=9, low=2, rng=1000, res=0.001)
        self['oPVcc'] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self['o12Vsbraw'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl_12Vsbraw'],
            sensor=self['o12Vsbraw'],
            detect_limit=(self.limits['InOCP'], ),
            ramp_range=sensor.RampRange(start=1.2, stop=2.3, step=0.1),
            delay=0.1)
        self['oOCP'].reset = False


class Measurements(share.Measurements):

    """Bias Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'olock', ''),
            ('dmm_400V', '400V', 'o400V', ''),
            ('dmm_pvcc', 'PVcc', 'oPVcc', ''),
            ('dmm_12Vsbraw', '12VsbRaw', 'o12Vsbraw', ''),
            ('dmm_12Vsbraw2', 'InOCP', 'o12Vsbraw', ''),
            ('ramp_OCP', 'OCP', 'oOCP', ''),
            ))
