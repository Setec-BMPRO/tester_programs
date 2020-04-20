#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""SMU750-70 Final Test Program."""

import tester

import share


class Final(share.TestSequence):

    """SMU750-70 Final Test Program."""

    limitdata = (
        tester.LimitDelta('70VOn', 70.0,  0.7),
        tester.LimitLow('70VOff', 69.2),
        tester.LimitDelta('OCP', 11.5, 0.1),
        tester.LimitLow('inOCP', 69.3),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('Shutdown', self._step_shutdown),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Switch on at 240Vac, measure output at min load."""
        dev['dcl'].output(0.0, output=True)
        dev['acsource'].output(240.0, output=True, delay=2.0)
        self.measure(('dmm_70Von', 'ui_YesNoFan', ), timeout=5)

    @share.teststep
    def _step_full_load(self, dev, mes):
        """Measure output at full load (11.3A +/- 150mA)."""
        dev['dcl'].output(11.2, delay=1)
        mes['dmm_70Von'](timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Measure OCP point."""
        mes['ramp_OCP']()

    @share.teststep
    def _step_shutdown(self, dev, mes):
        """Overload and shutdown unit, re-start."""
        dev['dcl'].output(11.9)
        mes['dmm_70Voff'](timeout=5)
        dev['dcl'].output(0.0, delay=2)
        mes['dmm_70Von'](timeout=10)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['dcl'] = tester.DCLoadParallel(
            ((tester.DCLoad(self.physical_devices['DCL1']), 1),
             (tester.DCLoad(self.physical_devices['DCL2']), 1),
             (tester.DCLoad(self.physical_devices['DCL3']), 1),
             (tester.DCLoad(self.physical_devices['DCL4']), 1)))

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
        self['o70V'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self['oYesNoFan'] = sensor.YesNo(
            message=tester.translate('smu75070_final', 'IsFanOn?'),
            caption=tester.translate('smu75070_final', 'capFanOn'))
        self['oOCP'] = sensor.Ramp(
            stimulus=self.devices['dcl'],
            sensor=self['o70V'],
            detect_limit=(self.limits['inOCP'], ),
            ramp_range=sensor.RampRange(start=11.3, stop=11.8, step=0.01),
            delay=0.1)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_70Von', '70VOn', 'o70V', ''),
            ('dmm_70Voff', '70VOff', 'o70V', ''),
            ('ui_YesNoFan', 'Notify', 'oYesNoFan', ''),
            ('ramp_OCP', 'OCP', 'oOCP', ''),
            ))
