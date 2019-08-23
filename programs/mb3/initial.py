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

    vaux = 12.8
    vsolar = 12.8

    limitdata = (
        tester.LimitBetween('Vaux', 8.0, 13.6),
        tester.LimitBetween('Vsolar', 8.0, 13.6),
        tester.LimitPercent('5V', 5.0, 1.0),
        tester.LimitDelta('Vbat', 14.6, 0.3),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('PgmAVR', self.devices['program_avr'].program),
            tester.TestStep('Initialise', self._step_initialise),
            tester.TestStep('Output', self._step_output),
            )
        self.sernum = None

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply input power and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vaux'].output(self.vaux, output=True)
        dev['dcl_vbat'].output(0.1, True)
        self.measure(('dmm_vaux', 'dmm_5v', 'dmm_vbat'), timeout=5)

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the unit."""
        # Cycle power to restart the unit
        dev['dcs_vaux'].output(0.0, delay=0.5)
        dev['dcs_vaux'].output(self.vaux, delay=1.0)

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output of the unit."""
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
                ('rla_reset', tester.Relay, 'RLA1'),
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
            config.fuses
            )

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_vaux', 'dcs_vsol'):
            self[dcs].output(0.0, False)
        self['dcl_vbat'].output(0.0, False)
        for rla in ('rla_reset', ):
            self[rla].set_off()


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
            ('dmm_vaux', 'Vaux', 'vaux', 'Aux power ok'),
            ('dmm_vsolar', 'Vsolar', 'vsolar', 'Solar input ok'),
            ('dmm_5v', '5V', '5V', '5V ok'),
            ('dmm_vbat', 'Vbat', 'vbat', 'Battery output ok'),
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ))
