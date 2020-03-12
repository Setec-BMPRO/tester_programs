#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 SETEC Pty Ltd
"""Trek2/JControl Initial Test Program."""

import inspect
import os

import serial
import tester

import share
from . import config, console


class Initial(share.TestSequence):

    """Trek2/JControl Initial Test Program."""

    # Startup voltage
    vin_start = 8.0
    # Input voltage to power the unit
    vin_set = 12.0
    # Common limits
    _common = (
        tester.LimitDelta('Vin', vin_start - 0.75, 0.5,
            doc='Input voltage present'),
        tester.LimitPercent('3V3', 3.3, 3.0, doc='3V3 present'),
        # CAN Bus is operational if status bit 28 is set
        tester.LimitInteger('CAN_BIND', 1 << 28, doc='CAN bus bound'),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    config_data = {
        'TK2': {
            'Config': config.Trek2,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.Trek2.sw_version.replace('.', r'\.'))),
                ),
            },
        'JC': {
            'Config': config.JControl,
            'Limits': _common + (
                tester.LimitRegExp('SwVer', '^{0}$'.format(
                    config.JControl.sw_version.replace('.', r'\.'))),
                ),
            },
        }

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.config = self.config_data[self.parameter]['Config']
        Devices.sw_image = self.config.sw_image
        super().open(
            self.config_data[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self.devices['programmer'].program),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(self.vin_start, output=True)
        self.measure(('dmm_vin', 'dmm_3v3'), timeout=5)
        dev['dcs_vin'].output(self.vin_set)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        dev['arm'].open()
        dev['arm'].brand(
            self.config.hw_version, self.sernum, dev['rla_reset'])
        mes['sw_ver']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['can_bind'](timeout=10)
        armtunnel = dev['armtunnel']
        armtunnel.open()
        mes['tunnel_swver']()
        armtunnel.close()


class Devices(share.Devices):

    """Devices."""

    sw_image = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS3'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        arm_port = share.config.Fixture.port('027420', 'ARM')
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, self.sw_image),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Direct Console driver
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = arm_port
        self['arm'] = console.DirectConsole(arm_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.SETECDeviceID.trek2)
        self['armtunnel'] = console.TunnelConsole(tunnel)

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        self['armtunnel'].close()
        self['dcs_vin'].output(0.0, output=False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        arm = self.devices['arm']
        armtunnel = self.devices['armtunnel']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'X207'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U4 output'
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trek2_jcontrol_initial', 'msgSnEntry'),
            caption=tester.translate('trek2_jcontrol_initial', 'capSnEntry'),
            timeout=300)
        self['sernum'].doc = 'Barcode scanner'
        # Console sensors
        self['canbind'] = sensor.KeyedReading(arm, 'CAN_BIND')
        self['swver'] = sensor.KeyedReadingString(arm, 'SW_VER')
        self['tunnelswver'] = sensor.KeyedReadingString(armtunnel, 'SW_VER')


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('can_bind', 'CAN_BIND', 'canbind', 'CAN bound'),
            ('sw_ver', 'SwVer', 'swver', 'Unit software version'),
            ('tunnel_swver', 'SwVer', 'tunnelswver', 'Unit software version'),
            ))
