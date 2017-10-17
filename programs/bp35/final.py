#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Final Test Program."""

import os
import serial
import tester
import share
from . import console
from . import config


class Final(share.TestSequence):

    """BP35 Final Test Program."""

    arm_version = config.ARM_SW_VERSION
    # Serial port for CAN interface
    can_port = {'posix': '/dev/ttyUSB0', 'nt': 'COM20'}[os.name]
    # CAN ID
    can_id = 16
    # Test limits
    limitdata = (
        tester.LimitDelta('Vbat', 12.8, 0.2, doc='Output voltage'),
        tester.LimitRegExp(
            'ARM-SwVer', '^{0}$'.format(arm_version.replace('.', r'\.')),
            doc='Software version'),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('CAN', self._step_can),
            )
        self.sernum = None

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit and measure output voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['acsource'].output(voltage=240.0, output=True)
        self.measure(('dmm_vbat', 'ui_yesnogreen',), timeout=10)

    @share.teststep
    def _step_can(self, dev, mes):
        """Access the unit console using the CAN bus."""
        bp35 = dev['bp35']
        bp35.open()
        mes['arm_swver']()
        # Set unit internal Serial Number to match the outside label
        bp35['SER_ID'] = self.sernum
        bp35['NVWRITE'] = True
        bp35.close()

class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        self['dmm'] = tester.DMM(self.physical_devices['DMM'])
        self['acsource'] = tester.ACSource(self.physical_devices['ACS'])
        port = serial.Serial(Final.can_port, baudrate=115200, timeout=0.1)
        tunnel = share.ConsoleCanTunnel(port, Final.can_id)
        self['bp35'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['bp35'].close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['vbat'] = tester.sensor.Vdc(
            self.devices['dmm'], high=2, low=2, rng=100, res=0.001)
        self['vbat'].doc = 'Unit output'
        bp35 = self.devices['bp35']
        self['arm_swver'] = console.Sensor(
            bp35, 'SW_VER', rdgtype=sensor.ReadingString)
        self['yesnogreen'] = sensor.YesNo(
            message=tester.translate('bp35_final', 'IsOutputLedGreen?'),
            caption=tester.translate('bp35_final', 'capOutputLed'))
        self['yesnogreen'].doc = 'Tester operator'
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bp35_final', 'msgSnEntry'),
            caption=tester.translate('bp35_final', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vbat', 'Vbat', 'vbat', 'Output ok'),
            ('ui_yesnogreen', 'Notify', 'yesnogreen', 'LED Green'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', 'Unit software version'),
            ))
