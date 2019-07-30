#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Final Program."""

import tester
from tester import TestStep, LimitBetween, LimitPercent
import share
from . import config


class Final(share.TestSequence):

    """MB3 Final Test Program."""

    vstart = 13.1
    vstop = 8.0

    limitdata = (
        LimitBetween('Vaux', 8.0, 13.5),
        LimitPercent('Vbat', 14.4, 3.0),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        Devices.arm_image = config.sw_image
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerOn', self._step_power_on),
            )
        self.sernum = None

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply input power and measure voltages."""
        dev['dcs_vaux'].output(self.vstart, True, delay=0.5)
        dev['dcl_vbat'].output(0.1, True)
        self.measure(
            ('dmm_vaux', 'ui_yesnolight', 'dmm_vbat'), timeout=5)
        dev['dcs_vaux'].output(self.vstop)
        self.measure(
            ('dmm_vaux', 'ui_yesnooff',), timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vaux', tester.DCSource, 'DCS2'),
                ('dcl_vbat', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['dcs_vaux'].output(0.0, False)
        self['dcl_vbat'].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vaux'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vbat'] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self['yesnolight'] = sensor.YesNo(
            message=tester.translate('mb3_final', 'IsLightOn?'),
            caption=tester.translate('mb3_final', 'capLight'))
        self['yesnooff'] = sensor.YesNo(
            message=tester.translate('mb3_final', 'IsLightOff?'),
            caption=tester.translate('mb3_final', 'capLight'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vaux', 'Vaux', 'vaux', 'Aux power ok'),
            ('dmm_vbat', 'Vbat', 'vbat', 'Battery output ok'),
            ('ui_yesnolight', 'Notify', 'yesnolight', ''),
            ('ui_yesnooff', 'Notify', 'yesnooff', ''),
            ))
