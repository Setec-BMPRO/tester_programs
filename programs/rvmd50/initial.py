#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 Initial Test Program."""

import inspect
import os

import tester

import share
from . import display


class Initial(share.TestSequence):

    """RVMD50 Initial Test Program."""

    vin_set = 8.1               # Input voltage to power the unit
    sw_file = 'rvmd50_1.6.bin'  # Device software
    testlimits = (              # Test limits
        tester.LimitBetween('Vin', 7.0, 8.0, doc='Input voltage present'),
        tester.LimitPercent('3V3', 3.3, 3.0, doc='3V3 present'),
        tester.LimitLow('BkLghtOff', 0.5, doc='Backlight off'),
        tester.LimitBetween('BkLghtOn', 2.5, 3.5, doc='Backlight on'),
        )

    def open(self, uut):
        """Prepare for testing."""
        Devices.sw_file = self.sw_file
        super().open(self.testlimits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self.devices['programmer'].program),
            tester.TestStep('Display', self._step_display),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        dev['rla_watchdog_disable'].set_on()
        dev['dcs_vin'].output(self.vin_set, output=True)
        self.measure(('dmm_vin', 'dmm_3v3'), timeout=5)

    @share.teststep
    def _step_display(self, dev, mes):
        """Test the LCD and Backlight."""
        dev['rla_reset'].pulse(0.1, delay=5)
        mes['dmm_bklghtoff'](timeout=5)
        with dev['display']:
            self.measure(('YesNoDisplayOk', 'dmm_bklghton'), timeout=5)


class Devices(share.Devices):

    """Devices."""

    sw_file = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_watchdog_disable', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.programmer.ARM(
            share.config.Fixture.port('029687', 'ARM'),
            os.path.join(folder, self.sw_file),
            crpmode=None,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self['can'].verbose = False
        self['display'] = display.DisplayControl(self['can'])
        self.add_closer(self.close_can)

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_watchdog_disable'):
            self[rla].set_off()

    def close_can(self):
        """Reset CAN system."""
        self['can'].rvc_mode = False
        self['can'].verbose = False


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'X1'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U1 output'
        self['bklght'] = sensor.Vdc(dmm, high=1, low=2, rng=10, res=0.01)
        self['bklght'].doc = 'Across backlight'
        self['YesNoDisplay'] = sensor.YesNo(
            message=tester.translate('rvmd50', 'DisplayCheck?'),
            caption=tester.translate('rvmd50', 'capDisplayCheck'))
        self['YesNoDisplay'].doc = 'Operator input'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('dmm_bklghtoff', 'BkLghtOff', 'bklght', 'Test backlight'),
            ('dmm_bklghton', 'BkLghtOn', 'bklght', 'Test backlight'),
            ('YesNoDisplayOk', 'Notify', 'YesNoDisplay', 'Button on'),
            ))
