#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MB2 Final Program."""

import tester
from tester import (
    TestStep,
    LimitDelta, LimitBoolean
    )
import share

LIMITS = (
    LimitDelta('Vout', 14.0, 1.0, doc=''),
    LimitBoolean('Notify', True, doc=''),
    )


class Final(share.TestSequence):

    """MB2 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerOn', self._step_power_on),
            )

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Power up unit."""
        dev['dcs_vin'].output(12.0, True)
        dev['dcl_vout'].output(1.0, True)
        self.measure(('dmm_vout', 'ui_yesno_green', ), timeout=5)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcl_vout', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
        self['dcl_vout'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vout'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['yesnogreen'] = sensor.YesNo(
            message=tester.translate('mb2_final', 'IsGreenOn?'),
            caption=tester.translate('mb2_final', 'capLedGreen'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vout', 'Vout', 'vout', ''),
            ('ui_yesno_green', 'Notify', 'yesnogreen', ''),
            ))
