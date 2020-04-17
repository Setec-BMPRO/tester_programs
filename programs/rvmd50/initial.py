#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 Initial Test Program."""

import inspect
import os

import tester

import share

from . import device


class Initial(share.TestSequence):

    """RVMD50 Initial Test Program."""

    # Input voltage to power the unit
    vin_set = 8.1
    # Device software
    sw_file = 'rvmd50_1.3.bin'
    # Test limits
    testlimits = (
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
            tester.TestStep('Program', self._step_program),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        dev['dcs_vin'].output(self.vin_set, True)
        self.measure(('dmm_vin', 'dmm_3v3'), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM."""
        dev['rla_wd'].disable()
        dev['programmer'].program()

    @share.teststep
    def _step_display(self, dev, mes):
        """Test the LCD.

        Put device into test mode.
        Check all segments and backlight.

        """
        self.measure(
            ('ui_yesnoon', 'dmm_bklghton', 'ui_yesnooff', 'dmm_bklghtoff'),
            timeout=5)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        dev['canreader'].enable = True


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
                ('rla_wd', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use this relay
        watchdog = self['rla_wd']
        watchdog.enable = watchdog.set_off
        watchdog.disable = watchdog.set_on
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.programmer.ARM(
            share.config.Fixture.port('029687', 'ARM'),
            os.path.join(folder, self.sw_file),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self['can'].verbose = False
        self['decoder'] = tester.CANPacketDevice()
        self['canreader'] = tester.CANReader(
            self['can'], self['decoder'], device.RVMD50Packet,
            name='CANThread')
        self['canreader'].verbose = False
        self['canreader'].start()
        self.add_closer(self.close_can)

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_wd'):
            self[rla].set_off()
        self['canreader'].enable = False

    def close_can(self):
        """Reset CAN system."""
        self['canreader'].halt()
        self['can'].rvc_mode = False
        self['can'].verbose = False


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['mir_can'] = sensor.MirrorReadingString()
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'X1'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U1 output'
        self['bklght'] = sensor.Vdc(dmm, high=1, low=2, rng=10, res=0.01)
        self['bklght'].doc = 'Across backlight'
        self['oYesNoOn'] = sensor.YesNo(
            message=tester.translate(
            'rvmd50_initial', 'PushButtonOn?'),
            caption=tester.translate('rvmd50_initial', 'capButtonOn'))
        self['oYesNoOn'].doc = 'Operator input'
        self['oYesNoOff'] = sensor.YesNo(
            message=tester.translate(
            'rvmd50_initial', 'PushButtonOff?'),
            caption=tester.translate('rvmd50_initial', 'capButtonOff'))
        self['oYesNoOff'].doc = 'Operator input'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('dmm_bklghtoff', 'BkLghtOff', 'bklght', 'Test backlight'),
            ('dmm_bklghton', 'BkLghtOn', 'bklght', 'Test backlight'),
            ('ui_yesnoon', 'Notify', 'oYesNoOn', 'Button on'),
            ('ui_yesnooff', 'Notify', 'oYesNoOff', 'Button off'),
            ))
