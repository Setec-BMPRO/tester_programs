#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101x Final Test Program."""

import tester

import share

from . import device


class Final(share.TestSequence):

    """RVMC101x Final Test Program."""

    limitdata = (
        tester.LimitBoolean('ButtonOk', True, doc='Ok entered'),
        tester.LimitBoolean('RetractPressed', True, doc='Button pressed'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('CanBus', self._step_canbus),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev['dcs_vin'].output(12.0, output=True, delay=1.0)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        dev['canreader'].enable = True
        # Tell user to push unit's button after clicking OK
        mes['ui_buttonpress']()
        # Wait for the button press
        mes['retract'](timeout=10)
# FIXME: What about tester.devlogical.CANPacketError exceptions?


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dcs_vin', tester.DCSource, 'DCS1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self['can'].verbose = True
        self['decoder'] = tester.CANPacket()
        self['canreader'] = device.CANReader(
            self['can'], self['decoder'], name='CANThread')
        self['canreader'].start()
        self.add_closer(self.close_can)

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
        self['canreader'].enable = False

    def close_can(self):
        """Reset CAN system."""
        self['canreader'].stop()
        self['can'].rvc_mode = False
        self['can'].verbose = False


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvmc101_final', 'msgSnEntry'),
            caption=tester.translate('rvmc101_final', 'capSnEntry'))
        self['ButtonPress'] = sensor.OkCan(     # Press the 'RET' button
            message=tester.translate('rvmc101_final', 'msgPressButton'),
            caption=tester.translate('rvmc101_final', 'capPressButton'))
        decoder = self.devices['decoder']
        self['retract'] = tester.sensor.CANPacket(
            decoder, 'retract', rdgtype=tester.sensor.ReadingBoolean)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ui_buttonpress', 'ButtonOk', 'ButtonPress', ''),
            ('retract', 'RetractPressed', 'retract',
                'RET button pressed'),
            ))