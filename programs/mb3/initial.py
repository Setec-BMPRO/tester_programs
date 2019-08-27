#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Initial Program."""

import inspect
import os

import tester

import share
from . import config


class Initial(share.TestSequence):

    """MB3 Initial Test Program."""

    limitdata = (
        tester.LimitDelta('Vaux', config.vaux, 0.5),
        tester.LimitPercent('5V', 5.0, 1.0),
        tester.LimitDelta('Vbat', 14.6, 0.3),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('PgmAVR', self.devices['program_avr'].program),
            tester.TestStep('Output', self._step_output),
            )
        self.sernum = None

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply input power and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vaux'].output(config.vaux, output=True, delay=0.5)
        self.measure(('dmm_vaux', 'dmm_5v'), timeout=5)

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output of the unit."""
        dev['dcl_vbat'].output(0.01, output=True)
        mes['dmm_vbat'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vaux', tester.DCSource, 'DCS2'),
                ('dcs_vsol', tester.DCSource, 'DCS3'),
                ('dcl_vbat', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial port for the ATtiny406. Used by programmer and comms module.
        avr_port = share.fixture.port('033633', 'AVR')
        # ATtiny406 device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_avr'] = share.programmer.AVR(
            avr_port,
            os.path.join(folder, config.sw_image),
            fuses=config.fuses
            )

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vaux', 'dcs_vsol', 'dcl_vbat', ):
            self[dev].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vaux'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vsolar'] = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.01)
        self['5V'] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.01)
        self['vbat'] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('mb3_initial', 'msgSnEntry'),
            caption=tester.translate('mb3_initial', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vaux', 'Vaux', 'vaux', 'Aux input ok'),
            ('dmm_5v', '5V', '5V', '5V ok'),
            ('dmm_vbat', 'Vbat', 'vbat', 'Battery output ok'),
            ('ui_serialnum', 'SerNum', 'SnEntry', 'Unit serial number'),
            ))
