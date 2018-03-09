#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Safety Test Program."""

import tester
import share
from tester import TestStep, LimitBetween


class Safety(share.TestSequence):

    """SX-750 Safety Test Program."""

    limitdata = (
        LimitBetween('gnd', 20, 100),
        LimitBetween('arc', -0.001, 0),
        LimitBetween('acw', 2.0, 4.0),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Gnd1', self._step_gnd1),
            TestStep('Gnd2', self._step_gnd2),
            TestStep('Gnd3', self._step_gnd3),
            TestStep('HiPot', self._step_hipot),
            )

    @share.teststep
    def _step_gnd1(self, dev, mes):
        """Ground Continuity 1."""
        mes['gnd1']()

    @share.teststep
    def _step_gnd2(self, dev, mes):
        """Ground Continuity 2."""
        mes['gnd2']()

    @share.teststep
    def _step_gnd3(self, dev, mes):
        """Ground Continuity 3."""
        mes['gnd3']()

    @share.teststep
    def _step_hipot(self, dev, mes):
        """HiPot Test."""
        mes['acw']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        self['st'] = tester.SafetyTester(self.physical_devices['SAF'])


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        st = self.devices['st']
        sensor = tester.sensor
        self['gnd1'] = sensor.STGND(st, step=1, ch=1)
        self['gnd2'] = sensor.STGND(st, step=2, ch=2, curr=11)
        self['gnd3'] = sensor.STGND(st, step=3, ch=3, curr=11)
        self['acw'] = sensor.STACW(st, step=4)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('gnd1', 'gnd', 'gnd1', ''),
            ('gnd2', 'gnd', 'gnd2', ''),
            ('gnd3', 'gnd', 'gnd3', ''),
            ))
        self['acw'] = tester.Measurement(
            (self.limits['arc'], self.limits['acw'], ),
            self.sensors['acw'], doc='')
