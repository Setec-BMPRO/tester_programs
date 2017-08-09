#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MB2 Final Program."""

import tester
from tester import (
    TestStep,
    LimitDelta, LimitPercent, LimitLow, LimitBoolean
    )
import share

VSTART = 12.8
VSTOP = 9.2

LIMITS = (
    LimitDelta('Vin', 12.8, 0.1),
    LimitPercent('Vout', 14.4, 3.0),
    LimitLow('VoutOff', 0.5),
    LimitBoolean('Notify', True),
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
        dev['dcs_vin'].output(VSTART, True)
        dev['dcl_vout'].output(1.0, True)
        mes['dmm_vin'].stable(delta=0.005)
        mes['dmm_vout'](timeout=5)
        dev['dcs_vin'].output(VSTOP)
        mes['ui_yesnolight'](timeout=5)


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
        self['vin'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['vout'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['yesnolight'] = sensor.YesNo(
            message=tester.translate('mb2_final', 'IsLightOn?'),
            caption=tester.translate('mb2_final', 'capLight'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_vout', 'Vout', 'vout', ''),
            ('dmm_voutoff', 'VoutOff', 'vout', ''),
            ('ui_yesnolight', 'Notify', 'yesnolight', ''),
            ))
