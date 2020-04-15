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

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, output=False)


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        sensor = tester.sensor
        self['yesnoseg'] = sensor.YesNo(
            message=tester.translate('rvview_jdisplay_final', 'AreSegmentsOn?'),
            caption=tester.translate('rvview_jdisplay_final', 'capSegments'))
        self['yesnoseg'].doc = 'Operator input'
        self['yesnobklght'] = sensor.YesNo(
            message=tester.translate('rvview_jdisplay_final', 'IsBacklightOk?'),
            caption=tester.translate('rvview_jdisplay_final', 'capBacklight'))
        self['yesnobklght'].doc = 'Operator input'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('ui_yesnoseg', 'Notify', 'yesnoseg', 'Segment display'),
            ('ui_yesnobklght', 'Notify', 'yesnobklght', 'Backlight'),
            ))
