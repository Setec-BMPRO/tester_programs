#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 Final Test Program."""

import tester

import share


class Final(share.TestSequence):

    """RVMD50 Final Test Program."""

    # Input voltage to power the unit
    vin_set = 12.0
    # Start up delay timer
    start_delay = 5.0

    def open(self, uut):
        """Prepare for testing."""
        super().open((), Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Display', self._step_display),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev['dcs_vin'].output(
            self.vin_set, output=True, delay=self.start_delay)

    @share.teststep
    def _step_display(self, dev, mes):
        """Display tests."""
        self.measure(('ui_yesnoseg', 'ui_yesnobklght', ))


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dcs_vin', tester.DCSource, 'DCS1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self['can'].verbose = False
        self['decoder'] = tester.CANPacketDevice()
        self['canreader'] = tester.CANReader(
            self['can'], self['decoder'], share.can.DeviceStatusPacket,
            name='CANThread')
        self['canreader'].verbose = False
        self['canreader'].start()
        self.add_closer(self.close_can)

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, output=False)
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
        sensor = tester.sensor
        self['yesnoseg'] = sensor.YesNo(
            message=tester.translate('rvmd50_final', 'AreSegmentsOn?'),
            caption=tester.translate('rvmd50_final', 'capSegments'))
        self['yesnoseg'].doc = 'Operator input'
        self['yesnobklght'] = sensor.YesNo(
            message=tester.translate('rvmd50_final', 'IsBacklightOk?'),
            caption=tester.translate('rvmd50_final', 'capBacklight'))
        self['yesnobklght'].doc = 'Operator input'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('ui_yesnoseg', 'Notify', 'yesnoseg', 'Segment display'),
            ('ui_yesnobklght', 'Notify', 'yesnobklght', 'Backlight'),
            ))
